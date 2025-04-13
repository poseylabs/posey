import EmailPassword from 'supertokens-auth-react/recipe/emailpassword'; // Keep this
import ThirdParty, { Google } from 'supertokens-auth-react/recipe/thirdparty'; // Import Google

import Session from 'supertokens-auth-react/recipe/session';
import { useRouter } from 'next/navigation';
import { SuperTokensConfig } from 'supertokens-auth-react/lib/build/types';

const routerInfo: { router?: ReturnType<typeof useRouter>; pathName?: string } =
{};

export function setRouter(
router: ReturnType<typeof useRouter>,
pathName: string,
) {
routerInfo.router = router;
routerInfo.pathName = pathName;
}

export const supertokensConfig = (): SuperTokensConfig => {
  return {
      appInfo: {
        appName: "Posey",
        apiDomain: "http://localhost:9999",
        websiteDomain: "http://localhost:8888",
        // apiBasePath: '/api/auth',
        // websiteBasePath: '/auth'
      },
      recipeList: [
        EmailPassword.init(),
        ThirdParty.init({
              signInAndUpFeature: {
                  providers: [
                      Google.init(),
                  ],
              },
          }),
          Session.init(),
      ],
    //   windowHandler: (orig) => {
    //       return {
    //           ...orig,
    //           location: {
    //               ...orig.location,
    //               getPathName: () => routerInfo.pathName!,
    //               assign: (url) => routerInfo.router!.push(url.toString()),
    //               setHref: (url) => routerInfo.router!.push(url.toString()),
    //           },
    //       };
    //   },
  };
}