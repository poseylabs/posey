import jwt from 'jsonwebtoken';
import { v4 as uuidv4 } from 'uuid';
import bcrypt from 'bcrypt';
import { Pool } from 'pg';
import { User, UserRole } from '../types/user';
import Defaults from '../config/defaults';

if (!process.env.DATABASE_URL) {
  throw new Error('Environment variable DATABASE_URL is not set.');
}

// Create a pool connection to the PostgreSQL database.
// The connection string can come from an environment variable or fallback to a default.
// Ensure your DATABASE_URL (or similar) is set appropriately to point to your @postgres container.
const pool = new Pool({
  connectionString:
    process.env.DATABASE_URL
});

/**
 * Check if the user has an admin role.
 *
 * @param user - The user object.
 * @returns True if the user is an admin; otherwise false.
 */
export function isAdmin(user: User): boolean {
  return user.role === UserRole.ADMIN;
}

/**
 * Check if the user has a specific role.
 *
 * @param user - The user object.
 * @param requiredRole - The role to check against.
 * @returns True if the user has the required role; otherwise false.
 */
export function hasRole(user: User, requiredRole: UserRole): boolean {
  return user.role === requiredRole;
}

/**
 * Decodes a JWT token without verifying it.
 *
 * @param token - The JWT token.
 * @returns The decoded payload.
 */
export function decodeJWT(token: string): any {
  return jwt.decode(token);
}

/**
 * Verifies a JWT token using a secret key.
 *
 * @param token - The JWT token.
 * @param secret - The secret key used to sign the token.
 * @returns The decoded payload upon successful verification.
 * @throws An error if verification fails.
 */
export function verifyJWT(token: string, secret: string): any {
  return jwt.verify(token, secret);
}

/* --------------------------------------------------------------------------
   Additional functions for updating, deleting, and changing a user's password.
--------------------------------------------------------------------------*/

/**
 * Updates a user's data.
 *
 * @param userId - The ID of the user to update.
 * @param updateData - A partial User object with properties to update.
 * @returns The updated User object.
 *
 * @remarks
 * This implementation uses the pg Pool to execute an UPDATE query.
 */
export async function updateUser(
  userId: string,
  updateData: Partial<User>
): Promise<User> {
  const keys = Object.keys(updateData);
  if (keys.length === 0) {
    throw new Error('No update data provided.');
  }

  // Build the SET clause dynamically while avoiding SQL injection.
  const setClauses = keys.map(
    (key, index) => `"${key}" = $${index + 1}`
  );
  // Append an updated_at field to the query.
  const query = `UPDATE users SET ${setClauses.join(
    ', '
  )}, updated_at = CURRENT_TIMESTAMP WHERE id = $${keys.length + 1} RETURNING *`;
  const values = keys.map((key) => updateData[key as keyof User]) as any[];
  values.push(userId);

  const result = await pool.query(query, values);
  if (result.rowCount === 0) {
    throw new Error('User not found.');
  }
  return result.rows[0];
}

/**
 * Deletes a user from the system.
 *
 * @param userId - The ID of the user to delete.
 *
 * @remarks
 * This function executes a DELETE query against the users table.
 */
export async function deleteUser(userId: string): Promise<void> {
  const result = await pool.query(`DELETE FROM users WHERE id = $1`, [userId]);
  if (result.rowCount === 0) {
    throw new Error('User not found.');
  }
}

/**
 * Changes a user's password by verifying the current password and updating to the new one.
 *
 * @param user - The user object (must include a hashedPassword).
 * @param oldPassword - The current password provided by the user.
 * @param newPassword - The new password to set.
 *
 * @remarks
 * This function verifies the existing password using bcrypt and then hashes the new
 * password before updating it in the database.
 */
export async function changePassword(
  user: User,
  oldPassword: string,
  newPassword: string
): Promise<void> {
  // Retrieve the stored hashed password from the database.
  const userRecord = await pool.query(
    `SELECT "hashedPassword" FROM users WHERE id = $1`,
    [user.id]
  );
  if (userRecord.rowCount === 0) {
    throw new Error('User not found.');
  }

  const storedHashedPassword = userRecord.rows[0].hashedPassword;
  const isMatch = await bcrypt.compare(oldPassword, storedHashedPassword);
  if (!isMatch) {
    throw new Error('Old password does not match.');
  }

  const saltRounds = 10;
  const newHashedPassword = await bcrypt.hash(newPassword, saltRounds);

  // Update the password in the database.
  await pool.query(
    `UPDATE users SET "hashedPassword" = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2`,
    [newHashedPassword, user.id]
  );
} 
