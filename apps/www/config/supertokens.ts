import { SuperTokensConfig } from 'supertokens-auth-react/lib/build/types';
import Session from 'supertokens-auth-react/recipe/session';
import EmailPassword from 'supertokens-auth-react/recipe/emailpassword';

const apiDomain = process.env.NEXT_PUBLIC_AUTH_API_ENDPOINT || "http://localhost:9999";
const websiteDomain = process.env.NEXT_PUBLIC_AUTH_BASE_URL || "http://localhost:8888";

export const frontendConfig: SuperTokensConfig = {
  appInfo: {
    appName: "Posey",
    apiDomain: apiDomain,
    websiteDomain: websiteDomain,
    apiBasePath: "/auth",
    websiteBasePath: "/auth"
  },
  getRedirectionURL: async (context) => {
    return undefined
  },
  recipeList: [
    EmailPassword.init({
      signInAndUpFeature: {
        signUpForm: {
          formFields: [
            { id: "email", label: "Email", optional: false },
            { id: "password", label: "Password", optional: false },
            { id: "username", label: "Username", optional: false }
          ]
        }
      },
      override: {
        functions: (originalImplementation) => {
          return {
            ...originalImplementation,
            signIn: async function (input) {
              const response = await originalImplementation.signIn(input);
              return response;
            }
          }
        }
      }
    }),
    Session.init({
      tokenTransferMethod: "cookie",
      override: {
        functions: (originalImplementation) => {
          return {
            ...originalImplementation,
            getUserId: async function (input) {
              try {
                const result = await originalImplementation.getUserId(input);
                return result;
              } catch (err) {
                console.error("getUserId error:", err);
                throw err;
              }
            }
          }
        }
      }
    }),
  ],
};
