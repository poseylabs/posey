import { shared_account_info } from "./_shared";
import { posey_config } from "../posey";

export const retail = [
  {
    "id": "amazon",
    "email": "posey@posey.ai",
    "auth": {
      ...shared_account_info.auth
    },
    "permissions": {
      "purchasing_allowed": true,
      "spending_limit": posey_config.limits.spending
    }
  }
]
