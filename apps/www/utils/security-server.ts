import { cookies as Cookies } from 'next/headers';

export const getAccessToken = async () => {
  const cookies = await Cookies();
  return cookies.get('sAccessToken')?.value;
};
