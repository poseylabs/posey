import { NextResponse } from "next/server";

// Logout route handler
export async function GET() {
  // Create response to manage cookies
  const response = NextResponse.json(
    {
      success: true,
      data: { message: "Logged out successfully" },
    },
    { status: 200 },
  );

  // Clear the authentication cookies
  response.cookies.delete("sAccessToken");
  response.cookies.delete("sIdToken");
  response.cookies.delete("sRefreshToken");
  response.cookies.delete("sAntiCsrfToken");
  response.cookies.delete("session"); // Assuming this was also set

  // Redirect using a header is not standard for GET logout, usually just delete cookies and respond or redirect client-side.
  // If redirection is needed, it should typically happen client-side after receiving the logout confirmation,
  // or use the `redirect` function from `next/navigation` if appropriate for the flow.
  // For now, just return the success response with cookies cleared.

  return response;
} 