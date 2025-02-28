import { poseyPool, validateDatabaseConnection } from './database';

// User sync function
export async function syncUserToDatabase(userId: string, email: string, formFields?: any) {
  console.log('syncUserToDatabase START', { userId, email, formFields, dsn: process.env.POSTGRES_DSN_POSEY });
  await validateDatabaseConnection();

  try {
    console.log('syncUserToDatabase input:', { userId, email, formFields });

    // Handle both array and object formats for username
    let username;
    if (formFields) {
      if (Array.isArray(formFields)) {
        username = formFields.find((f: any) => f.id === 'username')?.value;
      } else if (typeof formFields === 'object') {
        username = formFields.username;
      }
    }

    // Fallback to email prefix if no username provided
    username = username || email.split('@')[0];

    console.log('syncUserToDatabase username:', username);

    // First check if user exists in posey database by ID
    const checkQuery = `
      SELECT id, username, email FROM public.users WHERE id = $1;
    `;

    console.log('syncUserToDatabase checkQuery:', checkQuery, userId);

    const existingUserById = await poseyPool.query(checkQuery, [userId]);
    console.log('syncUserToDatabase existingUserById.rows:', existingUserById.rows);

    // Also check if there's already a user with this email but different ID
    const checkEmailQuery = `
      SELECT id, username, email FROM public.users WHERE email = $1 AND id != $2;
    `;
    const existingUserByEmail = await poseyPool.query(checkEmailQuery, [email, userId]);
    console.log('syncUserToDatabase existingUserByEmail.rows:', existingUserByEmail.rows);

    // If we have a user with this email but different ID, we need to handle the conflict
    if (existingUserByEmail.rows.length > 0) {
      console.log('Email already exists for a different user ID');

      // Option 1: Use a modified email for this user in our database
      // This keeps both users separate but with modified emails
      const modifiedEmail = `${email.split('@')[0]}+${userId.substring(0, 6)}@${email.split('@')[1]}`;
      email = modifiedEmail;
      console.log(`Using modified email: ${email}`);
    }

    // Before updating, check if the username is already taken by another user
    if (username) {
      const checkUsernameConflictQuery = `
        SELECT id FROM public.users WHERE username = $1 AND id != $2;
      `;
      const usernameConflictCheck = await poseyPool.query(checkUsernameConflictQuery, [username, userId]);

      if (usernameConflictCheck.rows.length > 0) {
        console.log('Username already exists for a different user ID');
        // Generate a unique username by appending part of the userId
        const uniqueUsername = `${username}_${userId.substring(0, 6)}`;
        username = uniqueUsername;
        console.log(`Using modified username: ${username}`);
      }
    }

    // Now handle user creation or update
    if (existingUserById.rows.length === 0) {
      // Check if username exists
      const checkUsernameQuery = `
        SELECT username FROM public.users WHERE username = $1;
      `;

      const usernameCheck = await poseyPool.query(checkUsernameQuery, [username]);

      // If username exists, generate a unique one
      let finalUsername = username;
      if (usernameCheck.rows.length > 0) {
        const timestamp = new Date().getTime().toString().slice(-4);
        finalUsername = `${username}${timestamp}`;
        console.log(`Username already exists, using generated username: ${finalUsername}`);
      }

      try {
        // Try to insert the user with the potentially modified username and email
        const insertQuery = `
          INSERT INTO public.users (
            id,
            email,
            username,
            created_at,
            updated_at,
            status,
            role,
            preferences,
            metadata,
            last_login
          ) VALUES (
            $1, $2, $3, NOW(), NOW(), 'active', 'user', '{}'::jsonb, '{}'::jsonb, NOW()
          );
        `;

        console.log('syncUserToDatabase insertQuery:', insertQuery, userId, email, finalUsername);

        await poseyPool.query(insertQuery, [userId, email, finalUsername]);
        console.log(`Created new user ${userId} with username ${finalUsername} and email ${email} in posey database`);
      } catch (insertError: any) {
        // If we still get a conflict error, attempt more comprehensive conflict resolution
        if (insertError.code === '23505') {
          console.log(`Conflict error on insert: ${insertError.constraint}`);

          // Handle different types of conflicts
          if (insertError.constraint === 'users_username_key') {
            // Handle username conflict with a more unique solution
            const randomString = Math.random().toString(36).substring(2, 8);
            finalUsername = `${username}_${randomString}`;

            const retryUsernameQuery = `
              INSERT INTO public.users (
                id, email, username, created_at, updated_at, status, role, preferences, metadata, last_login
              ) VALUES (
                $1, $2, $3, NOW(), NOW(), 'active', 'user', '{}'::jsonb, '{}'::jsonb, NOW()
              );
            `;

            await poseyPool.query(retryUsernameQuery, [userId, email, finalUsername]);
            console.log(`Created user on username retry with ${finalUsername}`);
          }
          else if (insertError.constraint === 'users_email_key') {
            // Handle email conflict with a more unique solution
            const randomString = Math.random().toString(36).substring(2, 6);
            const emailParts = email.split('@');
            const modifiedEmail = `${emailParts[0]}+${randomString}@${emailParts[1]}`;

            const retryEmailQuery = `
              INSERT INTO public.users (
                id, email, username, created_at, updated_at, status, role, preferences, metadata, last_login
              ) VALUES (
                $1, $2, $3, NOW(), NOW(), 'active', 'user', '{}'::jsonb, '{}'::jsonb, NOW()
              );
            `;

            await poseyPool.query(retryEmailQuery, [userId, modifiedEmail, finalUsername]);
            console.log(`Created user on email retry with ${modifiedEmail}`);
          }
          else {
            // Different constraint issue
            throw insertError;
          }
        } else {
          // If it's another error, throw it
          throw insertError;
        }
      }
    } else {
      // User exists, update their information
      const updateQuery = `
        UPDATE users
        SET
          email = $2,
          username = COALESCE($3, username),
          updated_at = NOW(),
          last_login = NOW()
        WHERE id = $1;
      `;
      console.log('syncUserToDatabase updateQuery:', updateQuery, userId, email, username);

      await poseyPool.query(updateQuery, [userId, email, username]);
      console.log(`Updated existing user ${userId} in posey database`);
    }
    console.log('syncUserToDatabase END - Success', { userId });
    return true;
  } catch (error) {
    console.error('Error syncing user to database:', error);
    console.error('Error details:', {
      userId,
      email,
      formFields
    });
    console.error('syncUserToDatabase END - Error', { userId, error });
    // Return false instead of throwing to prevent authentication flow interruption
    return false;
  }
}

// Update last login function
export async function updateLastLogin(userId: string) {
  console.log('updateLastLogin START', { userId });
  await validateDatabaseConnection();

  try {
    // Update only the last_login field for existing users
    const updateQuery = `
      UPDATE users
      SET last_login = NOW()
      WHERE id = $1;
    `;
    console.log('updateLastLogin query:', updateQuery, userId);

    await poseyPool.query(updateQuery, [userId]);
    console.log(`Updated last_login for user ${userId}`);
    return true;
  } catch (error) {
    console.error('Error updating last login:', error);
    return false;
  }
} 