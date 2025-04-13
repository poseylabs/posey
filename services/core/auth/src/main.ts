import express from 'express';
import cors from 'cors';
import supertokens from 'supertokens-node';
import { middleware, errorHandler } from 'supertokens-node/framework/express';
import { verifySession } from 'supertokens-node/recipe/session/framework/express';
import { config } from './config';
import UserMetadata from "supertokens-node/recipe/usermetadata";
import { SessionRequest } from 'supertokens-node/framework/express';
import SuperTokens from "supertokens-node";
import { poseyPool, validateDatabaseConnection } from './database';
import { supertokensConfig } from './config/supertokens';
import { syncUserToDatabase, updateLastLogin } from './user-utils';

const DEFAULT_USER_PREFERENCES = {
  language: 'en',
  theme: 'light',
  notifications: true,
  emailNotifications: true,
  smsNotifications: false
};

const DEFAULT_USER_PROFILE = {
  name: '',
  image: '',
  bio: '',
};

// Console log for debugging imports
console.log('Loaded modules:', {
  express: !!express,
  cors: !!cors,
  supertokens: !!supertokens,
  poseyPool: !!poseyPool,
  validateDatabaseConnection: !!validateDatabaseConnection,
  supertokensConfig: !!supertokensConfig,
  syncUserToDatabase: !!syncUserToDatabase,
  updateLastLogin: !!updateLastLogin
});

const app = express();

console.log('POSEY AUTH SERVER', {
  allowedOrigins: config.allowedOrigins,
  apiDomain: config.apiDomain,
  websiteDomain: config.websiteDomain,
});

console.log('Environment Configuration:', {
  AUTH_PORT: process.env.AUTH_PORT,
  AUTH_API_DOMAIN: process.env.AUTH_API_DOMAIN,
  AUTH_BASE_URL: process.env.AUTH_BASE_URL,
  ALLOWED_ORIGINS: process.env.ALLOWED_ORIGINS,
  SUPERTOKENS_CONNECTION_URI: process.env.SUPERTOKENS_CONNECTION_URI,
  GOOGLE_CLIENT_ID: process.env.GOOGLE_CLIENT_ID?.substring(0, 8) + '...', // Only show first 8 chars for security
});

// Initialize SuperTokens first
console.log("--- SuperTokens Config BEFORE init ---");
console.log(JSON.stringify(supertokensConfig, (key, value) =>
  typeof value === 'function' ? `[Function ${value.name || 'anonymous'}]` : value, 2));
// Specifically log the override function reference
try {
    // Find the EmailPassword recipe config by checking for signUpFeature
    const emailPasswordRecipe = supertokensConfig.recipeList.find((r: any) => r.config?.signUpFeature);
    if (emailPasswordRecipe && emailPasswordRecipe.config?.override?.apis) {
        // Temporarily call the apis function to inspect the returned object
        const tempOriginalImpl = { signUpPOST: () => console.log("Original signUpPOST called"), /* other methods */ };
        const apisResult = emailPasswordRecipe.config.override.apis(tempOriginalImpl);
        console.log("EmailPassword signUpPOST override function exists in config:", typeof apisResult.signUpPOST === 'function');
    } else {
        console.log("EmailPassword override or apis function NOT found in config object.");
    }
} catch (e) {
    console.error("Error inspecting SuperTokens config override structure:", e);
}
console.log("--- Initializing SuperTokens NOW ---");
supertokens.init(supertokensConfig);

// Then setup CORS with SuperTokens headers
app.use(
  cors({
    origin: (origin, callback) => {
      console.log('CORS Request:', {
        origin,
        allowedOrigins: config.allowedOrigins
      });

      if (!origin || config.allowedOrigins.includes(origin)) {
        callback(null, true);
      } else {
        console.warn('Blocked origin:', origin);
        callback(new Error('Not allowed by CORS'));
      }
    },
    credentials: true,
    allowedHeaders: ['content-type', ...supertokens.getAllCORSHeaders()],
    methods: ['GET', 'PUT', 'POST', 'DELETE', 'OPTIONS'],
    exposedHeaders: [...supertokens.getAllCORSHeaders()],
    maxAge: 86400
  })
);

// Always set Access-Control-Allow-Credentials header explicitly
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Credentials', 'true');
  next();
});

app.use(express.json());

// SuperTokens middleware
app.use(middleware());

// Health check endpoint
app.get('/health', (_, res) => {
  res.send({ status: 'healthy' });
});

// Add a debug endpoint
app.get('/auth/debug', (req, res) => {
  console.log('Debug request received');
  console.log('Headers:', req.headers);
  console.log('Cookies:', req.headers.cookie);

  res.json({
    status: 'OK',
    message: 'Debug information logged to server console',
    hasSessionHeader: !!req.headers.authorization,
    hasCookies: !!req.headers.cookie,
    allowedOrigins: config.allowedOrigins,
    apiDomain: config.apiDomain,
    websiteDomain: config.websiteDomain
  });
});

// Add a simple debug endpoint
app.get('/auth/debug-cookies', (req, res) => {
  // Set a test cookie
  res.cookie('debug-cookie', 'test-value', {
    httpOnly: false,
    secure: false,
    sameSite: 'lax',
    path: '/'
  });

  res.json({
    status: 'OK',
    message: 'Debug cookie set'
  });
});

// Add before errorHandler()
app.use((err: any, req: express.Request, res: express.Response, next: express.NextFunction) => {
  console.error('Global error:', err);

  if (res.headersSent) {
    return next(err);
  }

  // Improve error handling with more detailed responses
  let errorMessage = 'Internal server error';
  let errorDetails = null;
  let statusCode = 500;

  // Handle specific error types
  if (err.code === 'ECONNREFUSED' && err.syscall === 'connect') {
    errorMessage = 'Database connection failed';
    errorDetails = {
      service: 'PostgreSQL',
      host: err.address,
      port: err.port
    };
    statusCode = 503; // Service Unavailable
  } else if (err.message && err.message.includes('POSTGRES_DSN_POSEY')) {
    errorMessage = 'Database configuration missing';
    errorDetails = {
      missingEnv: 'POSTGRES_DSN_POSEY',
      envVars: {
        NODE_ENV: process.env.NODE_ENV || 'undefined',
        POSTGRES_DSN_POSEY: process.env.POSTGRES_DSN_POSEY ? 'defined' : 'undefined',
      }
    };
    statusCode = 500;
  }

  // Send detailed error response
  res.status(statusCode).json({
    status: "ERROR",
    message: errorMessage,
    details: errorDetails,
    timestamp: new Date().toISOString(),
    requestPath: req.path
  });
});

// Placeholder Admin Check Middleware (replace with actual logic)
const isAdmin = async (req: SessionRequest, res: express.Response, next: express.NextFunction) => {
  if (!req.session) {
    return res.status(401).send("Unauthorized: No session");
  }
  const userId = req.session.getUserId();
  try {
    // Query the database for the user's role
    const query = `SELECT role FROM public.users WHERE id = $1`;
    const result = await poseyPool.query(query, [userId]);

    if (result.rows.length === 0) {
      console.warn(`Admin check failed: User ${userId} not found in database.`);
      return res.status(403).send("Forbidden: User not found");
    }

    const userRole = result.rows[0].role;

    // Check if the user has the 'admin' role
    if (userRole === 'admin') {
      console.log(`Admin access granted for user ${userId}`);
      next(); // User is an admin, proceed
    } else {
      console.warn(`Admin access denied for user ${userId}. Role: ${userRole}`);
      return res.status(403).send("Forbidden: Admin access required");
    }
  } catch (error) {
    console.error(`Error checking admin status for user ${userId}:`, error);
    return res.status(500).send("Internal server error checking admin status");
  }
};

// Then SuperTokens error handler
app.use(errorHandler());

// Add a cookie inspection middleware that runs after SuperTokens handlers
app.use((req, res, next) => {
  const originalEnd = res.end;
  const originalWrite = res.write;
  const chunks: Buffer[] = [];

  // Override write
  res.write = function (chunk: any) {
    if (Buffer.isBuffer(chunk)) {
      chunks.push(chunk);
    } else {
      chunks.push(Buffer.from(chunk));
    }
    return originalWrite.apply(res, arguments as any);
  } as any;

  // Override end
  res.end = function (chunk: any) {
    if (chunk) {
      if (Buffer.isBuffer(chunk)) {
        chunks.push(chunk);
      } else {
        chunks.push(Buffer.from(chunk));
      }
    }

    // Log cookie-related headers
    if (res.getHeader('set-cookie')) {
      console.log('Setting cookies in response:', res.getHeader('set-cookie'));
    }

    return originalEnd.apply(res, arguments as any);
  } as any;

  next();
});

// Updated helper function to accept dbRole
function formatUserData(userId: string, userInfo: any, metadataResult: any, dbRole?: string): any {
  // Prioritize dbRole if provided, otherwise fallback to metadata or default
  const role = dbRole || metadataResult?.metadata?.role || 'anonymous';

  return {
    id: userId,
    email: userInfo?.emails[0],
    username: metadataResult?.metadata?.username || userInfo?.emails[0].split('@')[0],
    role: role, // Use the determined role
    lastLogin: new Date(), // Consider fetching this from DB too if needed
    createdAt: new Date(userInfo?.timeJoined),
    metadata: {
      preferences: metadataResult?.metadata?.preferences || {},
      profile: metadataResult?.metadata?.profile || {}
    }
  };
}

// Add session verification endpoints
app.get("/auth/session", verifySession({
  sessionRequired: false,
  antiCsrfCheck: false
}), async (req: SessionRequest, res, next) => { // Added next for error handling
  try {
    console.log("Session request received, session exists:", !!req.session);

    if (!req.session) {
      return res.status(401).json({
        status: "NO_SESSION",
        message: "No active session found"
      });
    }

    const session = req.session;
    const userId = session.getUserId();

    // Fetch user info and metadata from SuperTokens
    const userInfo = await SuperTokens.getUser(userId);
    const metadataResult = await UserMetadata.getUserMetadata(userId);

    // Fetch role from database
    let dbRole: string | undefined;
    try {
      const roleQuery = `SELECT role FROM public.users WHERE id = $1`;
      const roleResult = await poseyPool.query(roleQuery, [userId]);
      if (roleResult.rows.length > 0) {
        dbRole = roleResult.rows[0].role;
      }
    } catch (dbError) {
      console.error(`Failed to fetch role from DB for user ${userId}:`, dbError);
      // Decide how to handle DB error - maybe still return user data without role?
      // For now, we'll let it fall back in formatUserData
    }

    // Format user data including the database role
    const user = formatUserData(userId, userInfo, metadataResult, dbRole);

    // Update last login time in the background (fire and forget)
    updateLastLogin(userId).catch(err => console.error(`Failed to update last login for ${userId}:`, err));

    res.status(200).json({
      status: "OK",
      user: user,
      session: {
        userId: userId,
        sessionHandle: session.getHandle(),
        accessTokenPayload: session.getAccessTokenPayload(),
      }
    });
  } catch (error) {
    console.error('Error in /auth/session:', error);
    // Use the global error handler
    next(error);
  }
});

app.post("/auth/session/refresh", verifySession({
  sessionRequired: false,
  antiCsrfCheck: true,
}), async (req: SessionRequest, res) => {
  try {
    if (!req.session) {
      return res.status(401).json({
        status: "ERROR",
        message: "No session found"
      });
    }

    // Get fresh session data
    const session = req.session;
    const userId = session.getUserId();
    const userInfo = await SuperTokens.getUser(userId);

    return res.json({
      status: "OK",
      session: {
        handle: session.getHandle(),
      },
      user: userInfo
    });
  } catch (error) {
    console.error("Session refresh error:", error);
    return res.status(500).json({
      status: "ERROR",
      message: "Failed to refresh session"
    });
  }
});

app.post("/auth/preferences", verifySession(), async (req: SessionRequest & { body: any }, res) => {
  try {
    const session = req.session!;
    const userId = session.getUserId();
    const preferences = req.body;

    // Update user metadata with new preferences
    await UserMetadata.updateUserMetadata(userId, {
      preferences: preferences
    });

    return res.json({
      status: "OK",
      preferences
    });
  } catch (err) {
    console.error("Error updating preferences:", err);
    return res.status(500).json({
      status: "ERROR",
      message: "Failed to update preferences"
    });
  }
});

// Add with other session endpoints
app.post("/auth/signout", verifySession(), async (req: SessionRequest, res) => {
  let session = req.session!;
  await session.revokeSession();

  return res.json({
    status: "OK"
  });
});

// Add update user endpoint
app.put("/auth/user", verifySession(), async (req: SessionRequest & { body: any }, res) => {
  try {
    const session = req.session!;
    const userId = session.getUserId();
    const updates = req.body;

    // Update metadata with new user data
    const currentMetadata = await UserMetadata.getUserMetadata(userId);
    const cleanedMetadata = {
      ...currentMetadata.metadata,
      ...updates,
    };

    // Get fresh user data
    const userInfo = await SuperTokens.getUser(userId);
    const updatedMetadata = await UserMetadata.getUserMetadata(userId);

    // Clean metadata
    const cleanedUpdatedMetadata = {
      ...cleanedMetadata,
      preferences: updatedMetadata.metadata?.preferences || DEFAULT_USER_PREFERENCES,
      profile: updatedMetadata.metadata?.profile || DEFAULT_USER_PROFILE
    };

    // Update user metadata in database
    await UserMetadata.updateUserMetadata(userId, cleanedUpdatedMetadata);

    return res.json({
      status: "OK",
      user: formatUserData(userId, userInfo, updatedMetadata)
    });
  } catch (err) {
    console.error("Error updating user:", err);
    return res.status(500).json({
      status: "ERROR",
      message: "Failed to update user"
    });
  }
});

// Add this endpoint to expose the JWT verification key
app.get("/auth/jwt/key", (_, res) => {
  // This should return the public key or secret used to verify JWTs
  res.json({
    key: process.env.JWT_SECRET_KEY || config.supertokens.apiKey
  });
});

app.get("/auth/test-cookie", (req, res) => {
  res.cookie("test-cookie", "value", {
    httpOnly: true,
    secure: false,  // true in production
    sameSite: "lax"
  });
  res.json({ success: true });
});

// Invite Code Management Routes

// POST /admin/invite-codes - Add a new invite code (Admin only)
app.post("/admin/invite-codes", verifySession(), isAdmin, async (req, res, next) => {
  const { inviteCode } = req.body;
  if (!inviteCode || typeof inviteCode !== 'string') {
    return res.status(400).json({ status: "ERROR", message: "inviteCode (string) is required in body" });
  }

  try {
    const insertQuery = `INSERT INTO invite_codes (code) VALUES ($1) ON CONFLICT (code) DO NOTHING`;
    const result = await poseyPool.query(insertQuery, [inviteCode]);
    if (result.rowCount !== null && result.rowCount > 0) {
      console.log(`Admin added invite code: ${inviteCode}`);
      res.status(201).json({ status: "OK", message: "Invite code added successfully" });
    } else {
      res.status(409).json({ status: "ERROR", message: "Invite code already exists" });
    }
  } catch (error) {
    console.error("Error adding invite code:", error);
    next(error); // Pass error to global handler
  }
});

// GET /admin/invite-codes - List all invite codes (Admin only)
app.get("/admin/invite-codes", verifySession(), isAdmin, async (req, res, next) => {
  try {
    const selectQuery = `SELECT code, created_at FROM invite_codes ORDER BY created_at DESC`;
    const result = await poseyPool.query(selectQuery);
    res.status(200).json({ status: "OK", inviteCodes: result.rows });
  } catch (error) {
    console.error("Error fetching invite codes:", error);
    next(error); // Pass error to global handler
  }
});

// DELETE /admin/invite-codes - Delete an invite code (Admin only)
app.delete("/admin/invite-codes", verifySession(), isAdmin, async (req, res, next) => {
  const { inviteCode } = req.body;
  if (!inviteCode || typeof inviteCode !== 'string') {
    return res.status(400).json({ status: "ERROR", message: "inviteCode (string) is required in body" });
  }

  try {
    const deleteQuery = `DELETE FROM invite_codes WHERE code = $1`;
    const result = await poseyPool.query(deleteQuery, [inviteCode]);
    if (result.rowCount !== null && result.rowCount > 0) {
      console.log(`Admin deleted invite code: ${inviteCode}`);
      res.status(200).json({ status: "OK", message: "Invite code deleted successfully" });
    } else {
      res.status(404).json({ status: "ERROR", message: "Invite code not found" });
    }
  } catch (error) {
    console.error("Error deleting invite code:", error);
    next(error); // Pass error to global handler
  }
});

// GET /auth/verify-invite - Verify an invite code (Public)
app.get("/auth/verify-invite", async (req, res, next) => {
  const inviteCode = req.query.code as string;
  if (!inviteCode) {
    return res.status(400).json({ status: "ERROR", message: "code query parameter is required" });
  }

  try {
    const verifyQuery = `SELECT code FROM invite_codes WHERE code = $1`;
    const verifyResult = await poseyPool.query(verifyQuery, [inviteCode]);
    const isValid = verifyResult.rows.length > 0;
    res.status(200).json({ status: "OK", isValid });
  } catch (error) {
    console.error("Error verifying invite code:", error);
    next(error); // Pass error to global handler
  }
});

const port = config.port;
app.listen(port, () => {
  console.log('Auth Server Configuration:', {
    port,
    apiDomain: config.apiDomain,
    websiteDomain: config.websiteDomain,
    allowedOrigins: config.allowedOrigins,
    supertokensURI: config.supertokens.connectionURI,
  });
}); 
