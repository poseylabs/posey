import { shared_account_info } from "./_shared";

const EMAIL_HOST = "arrow.mxrouting.net";
const IMAP_PORT = 993;
const SMTP_PORT = 465;
const USE_TLS = true;

const DEFAULT_SERVER = {
  "host": EMAIL_HOST,
  "port": IMAP_PORT,
  "use_tls": USE_TLS
}


export const email = {
  "email": shared_account_info.auth.email,
  "password": shared_account_info.auth.password,
  "access_info": {
    "imap": DEFAULT_SERVER,
    "smtp": {
      ...DEFAULT_SERVER,
      "port": SMTP_PORT,
    }
  }
}
