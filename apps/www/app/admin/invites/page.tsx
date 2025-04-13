'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  listInviteCodes,
  addInviteCode,
  deleteInviteCode,
} from '@posey.ai/core/helpers';

interface InviteCode {
  code: string;
  created_at: string;
}

export default function AdminInvitesPage() {
  const [inviteCodes, setInviteCodes] = useState<InviteCode[]>([]);
  const [newCode, setNewCode] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isAdding, setIsAdding] = useState(false);

  const fetchCodes = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const codes = await listInviteCodes();
      setInviteCodes(codes);
    } catch (err: any) {
      console.error('Failed to fetch invite codes:', err);
      setError(err.message || 'Failed to load invite codes.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCodes();
  }, [fetchCodes]);

  const handleAddCode = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCode.trim()) return;
    setIsAdding(true);
    setError(null);
    try {
      const success = await addInviteCode(newCode.trim());
      if (success) {
        setNewCode('');
        // Refresh the list after adding
        await fetchCodes();
      } else {
        // Handle potential errors like code already exists (though backend handles conflict)
        setError('Failed to add invite code. It might already exist.');
      }
    } catch (err: any) {
      console.error('Failed to add invite code:', err);
      setError(err.message || 'An error occurred while adding the code.');
    } finally {
      setIsAdding(false);
    }
  };

  const handleDeleteCode = async (codeToDelete: string) => {
    if (!confirm(`Are you sure you want to delete the invite code "${codeToDelete}"?`)) {
      return;
    }
    setError(null);
    try {
      const success = await deleteInviteCode(codeToDelete);
      if (success) {
        // Refresh the list after deleting
        await fetchCodes();
      } else {
        setError('Failed to delete invite code.');
      }
    } catch (err: any) {
      console.error('Failed to delete invite code:', err);
      setError(err.message || 'An error occurred while deleting the code.');
    }
  };

  return (
    <div>
      <h2 className="text-2xl font-semibold mb-4">Manage Invite Codes</h2>

      {/* Add New Code Form */}
      <form onSubmit={handleAddCode} className="mb-6 p-4 border rounded-md bg-base-100">
        <h3 className="text-lg font-medium mb-2">Add New Invite Code</h3>
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={newCode}
            onChange={(e) => setNewCode(e.target.value)}
            placeholder="Enter new invite code"
            className="input input-bordered w-full max-w-xs"
            required
            disabled={isAdding}
          />
          <button type="submit" className="btn btn-primary" disabled={isAdding || !newCode.trim()}>
            {isAdding ? <span className="loading loading-spinner"></span> : 'Add Code'}
          </button>
        </div>
      </form>

      {/* Display Errors */}
      {error && <div className="alert alert-error shadow-lg mb-4">{error}</div>}

      {/* Invite Codes Table */}
      {isLoading ? (
        <div className="text-center p-4"><span className="loading loading-lg"></span></div>
      ) : (
        <div className="overflow-x-auto">
          <table className="table w-full">
            <thead>
              <tr>
                <th>Invite Code</th>
                <th>Created At</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {inviteCodes.length > 0 ? (
                inviteCodes.map((code) => (
                  <tr key={code.code}>
                    <td><code>{code.code}</code></td>
                    <td>{new Date(code.created_at).toLocaleString()}</td>
                    <td>
                      <button
                        onClick={() => handleDeleteCode(code.code)}
                        className="btn btn-error btn-sm"
                        aria-label={`Delete invite code ${code.code}`}
                      >
                        Delete
                      </button>
                      {/* Add Edit button/functionality here if needed */}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={3} className="text-center">No invite codes found.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
} 