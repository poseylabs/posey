import Session from 'supertokens-node/recipe/session';
import EmailPassword from 'supertokens-node/recipe/emailpassword';
import ThirdPartyEmailPassword from 'supertokens-node/recipe/thirdpartyemailpassword';
import Dashboard from 'supertokens-node/recipe/dashboard';
import UserMetadata from "supertokens-node/recipe/usermetadata";
import { config } from '../config';
import { syncUserToDatabase, updateLastLogin } from '../user-utils';
import { poseyPool } from '../database';

// Console log for debugging imports
console.log('Supertokens config loaded modules:', {
  syncUserToDatabase: !!syncUserToDatabase,
  updateLastLogin: !!updateLastLogin,
  poseyPool: !!poseyPool
});

export const supertokensConfig: any = {
  framework: "express",
  supertokens: {
    connectionURI: config.supertokens.connectionURI || "http://posey-supertokens:3567",
    apiKey: config.supertokens.apiKey,
  },
  appInfo: {
    appName: "Posey",
    apiDomain: config.apiDomain,
    websiteDomain: config.websiteDomain,
  },
  cookieSecure: process.env.NODE_ENV === "production",
  cookieSameSite: process.env.COOKIE_SAME_SITE || "lax",
  cookieDomain: process.env.COOKIE_DOMAIN || ".posey.ai",
  getRedirectionURL: (context: any) => {
    let url = context.url;
    if (context.action === "SUCCESS" && context.newSessionCreated) {
      url = `/`;
    } else {
      url = `/auth/login`;
    }
    console.log('Redirect to:', url);
  },
  recipeList: [
    EmailPassword.init({
      signUpFeature: {
        formFields: [
          { id: "email", optional: false },
          {
            id: "password",
            optional: false,
            validate: async (password) => {
              if (password.length < 8) {
                return "Password must be at least 8 characters long";
              }
              return undefined;
            }
          },
          { id: "username", optional: false }
        ]
      },
      override: {
        apis: (originalImplementation: any) => ({
          ...originalImplementation,
          signUpPOST: async (input: any) => {
            if (!originalImplementation.signUpPOST) {
              throw new Error("signUpPOST not implemented");
            }
            const response = await originalImplementation.signUpPOST(input);

            if (response.status === "OK" && response.user.emails?.[0]) {
              await syncUserToDatabase(
                response.user.id,
                response.user.emails[0],
                input.formFields
              );
            }
            if (response.status === "OK") {
              delete response.redirectToPath;
            }
            return response;
          },
          signInPOST: async (input) => {
            const response = await originalImplementation?.signInPOST?.(input);
            if (response?.status === "OK" && response?.user) {
              const userId = response.user.id;
              const email = response.user?.emails[0];

              try {
                // Check if user already exists in our database
                const checkQuery = `
                  SELECT id FROM public.users WHERE id = $1;
                `;
                const existingResult = await poseyPool.query(checkQuery, [userId]);
                const userExists = existingResult.rows.length > 0;

                if (userExists) {
                  // User already exists, just update last login timestamp
                  console.log("Sign-in: User exists in database, updating last login");
                  await updateLastLogin(userId);
                } else {
                  // New user, perform full sync to create the user
                  console.log("Sign-in: User doesn't exist in database, performing full sync");
                  await syncUserToDatabase(
                    userId,
                    email,
                    response.user.loginMethods?.[0]?.recipeUserId?.getMetadata?.()
                  );
                }
              } catch (error) {
                console.error("Error in signInPOST checking user existence:", error);
                // Continue anyway to not block sign-in process
              }
            }

            if (response.status === "OK") {
              delete response.redirectToPath;
            }
            return response;
          }
        })
      }
    }),
    ThirdPartyEmailPassword.init({
      providers: [{
        config: {
          thirdPartyId: "google",
          clients: [{
            clientId: config.oauth.google.clientId,
            clientSecret: config.oauth.google.clientSecret
          }]
        }
      }],
      override: {
        apis: (originalImplementation: any) => ({
          ...originalImplementation,
          signInUpPOST: async (input: any) => {
            const response = await originalImplementation?.signInUpPOST?.(input);
            if (response?.status === "OK" && response?.user) {
              const userId = response.user.id;
              const email = response.user.email;

              try {
                // Check if user already exists in our database
                const checkQuery = `
                  SELECT id FROM public.users WHERE id = $1;
                `;
                const existingResult = await poseyPool.query(checkQuery, [userId]);
                const userExists = existingResult.rows.length > 0;

                if (userExists) {
                  // User already exists, just update last login timestamp
                  console.log("OAuth Sign-in: User exists in database, updating last login");
                  await updateLastLogin(userId);
                } else {
                  // New user, perform full sync to create the user
                  console.log("OAuth Sign-in: User doesn't exist in database, performing full sync");
                  await syncUserToDatabase(
                    userId,
                    email,
                    { username: email.split('@')[0] }
                  );
                }
              } catch (error) {
                console.error("Error in signInUpPOST checking user existence:", error);
                // Continue anyway to not block sign-in process
              }
            }
            return response;
          }
        })
      }
    }),
    Session.init({
      getTokenTransferMethod: () => "cookie",
      cookieSecure: process.env.NODE_ENV === "production",
      cookieSameSite: "lax",
      exposeAccessTokenToFrontendInCookieBasedAuth: true,
      override: {
        functions: (originalImplementation) => ({
          ...originalImplementation,
          createNewSession: async function (input) {
            console.log("Creating new session for user:", input.userId);

            input.accessTokenPayload = {
              ...input.accessTokenPayload,
              "st-jwt": true
            };

            return originalImplementation.createNewSession(input);
          }
        })
      }
    }),
    Dashboard.init({
      apiKey: config.dashboard.apiKey,
      admins: config.dashboard.admins,
    }),
    UserMetadata.init(),
  ],
}; 
