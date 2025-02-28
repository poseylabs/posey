import { useState, useEffect, useCallback } from 'react';
import { Message } from '@posey.ai/core';

interface BackgroundTask {
  task_id: string;
  task_type: string;
  status: string;
  progress: number;
  current_step?: string;
  result?: any;
  conversation_id: string;
}

interface UseBackgroundTasksProps {
  conversationId?: string;
  onTaskComplete?: (task: BackgroundTask) => void;
  pollInterval?: number;
}

export function useBackgroundTasks({
  conversationId,
  onTaskComplete,
  pollInterval = 5000
}: UseBackgroundTasksProps) {
  const [tasks, setTasks] = useState<BackgroundTask[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTasks = useCallback(async () => {
    if (!conversationId) return;

    console.log("useBackgroundTasks:fetchTasks", {
      conversationId
    })

    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_AGENT_API_ENDPOINT}/tasks/conversation/${conversationId}`,
        {
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch background tasks');
      }

      const data = await response.json();
      setTasks(data.tasks);

      // Check for completed tasks and call onTaskComplete
      data.tasks.forEach((task: BackgroundTask) => {
        if (task.status === 'completed' && onTaskComplete) {
          onTaskComplete(task);
        }
      });

    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  }, [conversationId, onTaskComplete]);

  useEffect(() => {
    if (!conversationId) return;

    // Initial fetch
    fetchTasks();

    // Set up polling
    const intervalId = setInterval(fetchTasks, pollInterval);

    return () => {
      clearInterval(intervalId);
    };
  }, [conversationId, fetchTasks, pollInterval]);

  return {
    tasks,
    isLoading,
    error,
    refetch: fetchTasks
  };
} 
