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

// Add helper function to format user data
function formatUserData(userId: string, userInfo: any, data: any): any {
  return {
    id: userId,
    email: userInfo?.emails[0],
    username: data?.metadata?.username || userInfo?.emails[0].split('@')[0],
    role: data?.metadata?.role || 'anonymous',
    lastLogin: new Date(),
    createdAt: new Date(userInfo?.timeJoined),
    metadata: {
      preferences: data?.metadata?.preferences || {},
      profile: data?.metadata?.profile || {}
    }

  };
}

// Add session verification endpoints
app.get("/auth/session", verifySession({
  sessionRequired: false,
  antiCsrfCheck: false
}), async (req: SessionRequest, res) => {
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
    console.log("Session userId:", userId);

    const userInfo = await SuperTokens.getUser(userId);
    console.log("User info retrieved:", !!userInfo);

    if (!userInfo?.emails?.[0]) {
      console.log("Invalid user data - no email found");
      return res.status(400).json({
        status: "ERROR",
        message: "Invalid user data"
      });
    }

    // Get metadata first to use existing username if available
    const metadata = await UserMetadata.getUserMetadata(userId);
    console.log("User metadata retrieved:", !!metadata);

    // First check if user already exists in our database
    try {
      const checkQuery = `
        SELECT id FROM public.users WHERE id = $1;
      `;
      const existingResult = await poseyPool.query(checkQuery, [userId]);
      const userExists = existingResult.rows.length > 0;

      if (userExists) {
        // User already exists, just update last login timestamp
        console.log("User exists in database, updating last login");
        await updateLastLogin(userId);
      } else {
        // New user, perform full sync to create the user
        console.log("User doesn't exist in database, performing full sync");
        await syncUserToDatabase(
          userId,
          userInfo.emails[0],
          {
            username: metadata?.metadata?.username || userInfo.emails[0].split('@')[0]
          }
        );
      }
    } catch (error) {
      console.error("Error checking user existence:", error);
      // Continue anyway to not block login process
    }

    // Even if sync fails, we still want to return user data if we have it
    return res.json({
      status: "OK",
      user: formatUserData(userId, userInfo, metadata),
      session: {
        sessionHandle: session.getHandle(),
      }
    });
  } catch (error) {
    console.error("Session error:", error);
    return res.status(500).json({
      status: "ERROR",
      message: "Failed to get session information"
    });
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

app.post("/auth/preferences", verifySession(), async (req: SessionRequest, res) => {
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
app.put("/auth/user", verifySession(), async (req: SessionRequest, res) => {
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
