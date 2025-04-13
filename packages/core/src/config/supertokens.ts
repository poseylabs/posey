import Session from 'supertokens-auth-react/recipe/session';
import EmailPassword from 'supertokens-auth-react/recipe/emailpassword'; // Keep this
import ThirdParty, { Google } from 'supertokens-auth-react/recipe/thirdparty'; // Import Google
import type { SuperTokensConfig, GetRedirectionURLContext as STGetRedirectionURLContext } from 'supertokens-auth-react/lib/build/types';

// Type for the getRedirectionURL context
export type GetRedirectionURLContext = STGetRedirectionURLContext;

interface CreateSupertokensFrontendConfigParams {
  appName: string;
  apiDomain?: string;
  websiteDomain?: string;
  apiBasePath?: string;
  websiteBasePath?: string;
  getRedirectionURL?: (context: GetRedirectionURLContext) => Promise<string | undefined>;
}

export function createSupertokensFrontendConfig({
  appName,
  apiDomain = process?.env?.NEXT_PUBLIC_AUTH_API_ENDPOINT ?? 'http://localhost:9999',
  websiteDomain = process?.env?.NEXT_PUBLIC_APP_BASE_URL ?? 'http://localhost:8888',
  apiBasePath,
  websiteBasePath,
  getRedirectionURL,
}: CreateSupertokensFrontendConfigParams): SuperTokensConfig {

  return {
    appInfo: {
      appName,
      apiDomain,
      websiteDomain,
      apiBasePath,
      websiteBasePath,
    },
    getRedirectionURL: getRedirectionURL ? async (context) => getRedirectionURL(context) : undefined,
    recipeList: [
      EmailPassword.init(), // Initialize EmailPassword
      ThirdParty.init({
        signInAndUpFeature: {
          providers: [
            Google.init(), // Initialize Google provider
            // Add other providers like GitHub.init() here if needed
          ],
        },
      }),
      Session.init({
        tokenTransferMethod: "cookie",
      }),
    ],
  };
} 