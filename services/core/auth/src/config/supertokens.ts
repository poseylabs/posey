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
  // cookieSecure: process.env.NODE_ENV === "production",
  // cookieSameSite: "none",
  // cookieDomain: process.env.COOKIE_DOMAIN || ".posey.ai",
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
          { id: "username", optional: false },
          { id: "inviteCode", optional: false }
        ]
      },
      override: {
        apis: (originalImplementation: any) => ({
          ...originalImplementation,
          signUpPOST: async (input: any) => {
            // Log the received formFields
            console.log("signUpPOST Override: Received formFields:", JSON.stringify(input?.formFields, null, 2));

            if (!originalImplementation.signUpPOST) {
              throw new Error("signUpPOST not implemented");
            }

            const formFields = input.formFields;

            // Ensure formFields exist and are an array
            if (!Array.isArray(formFields)) {
              console.error("signUpPOST Override: formFields is missing or not an array in input.");
              return {
                status: "GENERAL_ERROR",
                message: "Internal server error: Invalid request format."
              };
            }

            // Extract inviteCode from the formFields array
            const inviteCodeField = formFields.find((f: any) => f.id === "inviteCode");
            const inviteCode = inviteCodeField?.value;

            console.log(`signUpPOST Override: Extracted inviteCode: ${inviteCode}`);

            if (!inviteCode) {
              console.log("signUpPOST Override: Invite code check failed (missing from formFields or empty).");
              return {
                status: "GENERAL_ERROR",
                message: "Invite code is required"
              };
            }

            try {
              // 1. Validate Invite Code
              const verifyQuery = `SELECT code FROM invite_codes WHERE code = $1`;
              const verifyResult = await poseyPool.query(verifyQuery, [inviteCode]);

              if (verifyResult.rows.length === 0) {
                return {
                  status: "GENERAL_ERROR",
                  message: "Invalid invite code"
                };
              }

              // 2. Call Original SuperTokens Implementation (with ORIGINAL fields)
              // No need to filter since inviteCode is now declared in config
              // const filteredFormFields = formFields.filter((f: any) => f.id !== "inviteCode");

              // Pass the original input directly, or construct with all expected fields
              // Option 1: Pass original input (assuming it's safe)
              const originalInput = input;
              // Option 2 (Slightly safer if Option 1 fails): Reconstruct with formFields, tenantId, userContext
              // const originalInput = {
              //   formFields: formFields,
              //   tenantId: input.tenantId,
              //   userContext: input.userContext
              // };

              // Remove logging of the potentially circular originalInput object
              // console.log("Calling original signUpPOST with input:", JSON.stringify(originalInput, null, 2));
              const response = await originalImplementation.signUpPOST(originalInput);
              // Remove logging of the potentially circular response object
              // console.log("Original signUpPOST response:", JSON.stringify(response, null, 2));

              // Log specific, safe response properties if needed for debugging
              console.log(`Original signUpPOST response status: ${response?.status}`);
              if (response?.status === 'OK' && response?.user) {
                console.log(`Original signUpPOST response user ID: ${response.user.id}`);
              }

              // 3. Post-Signup Actions (Sync user, Delete invite code)
              if (response.status === "OK" && response.user && response.user.email) {
                // Find username from the ORIGINAL formFields (which includes username)
                const usernameField = formFields.find((f: any) => f.id === 'username');
                const username = usernameField ? usernameField.value : undefined;

                await syncUserToDatabase(
                  response.user.id,
                  response.user.email,
                  username
                );
                console.log(`User ${response.user.id} synced to database.`);

                const deleteQuery = `DELETE FROM invite_codes WHERE code = $1`;
                await poseyPool.query(deleteQuery, [inviteCode]);
                console.log(`Invite code ${inviteCode} used and deleted.`);
              } else if (response.status !== "OK") {
                console.error("Original signUpPOST failed:", response);
              }

              return response;
            } catch (error) {
              console.error("Error during sign up override:", error);
              return {
                status: "GENERAL_ERROR",
                message: "An error occurred during sign up. Please try again."
              };
            }
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
      cookieSecure: false,
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
