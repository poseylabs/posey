import { shared_account_info } from "./_shared";

export const social = [
  {
    "id": "twitter",
    "email": shared_account_info.auth.email,
    "auth": {
      ...shared_account_info.auth
    }
  }
]
