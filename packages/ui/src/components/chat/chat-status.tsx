import { useState, useEffect } from 'react';

export function ChatStatus({
  status,
  message
}: {
  status: string;
  message: string;
}) {
  // Initialize progress state
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    // When status is 'loading', start an interval to animate progress
    let timer: number | null = null;
    if (status === 'loading') {
      timer = window.setInterval(() => {
        // Increment progress by 10 every 100ms; reset to 0 if reaching or exceeding 100 to loop the animation
        setProgress((current) => (current >= 100 ? 0 : current + 2));
      }, 100);
    } else {
      // If not loading, set progress to complete (100)
      setProgress(100);
    }

    // Clear the interval when component unmounts or when status changes
    return () => {
      if (timer !== null) {
        clearInterval(timer);
      }
    };
  }, [status]);

  if (status === 'error') {
    return (
      <div className="flex flex-col items-center gap-2 mb-4 justify-center">
        <div className="flex items-center gap-2">
          <h6 className="text-sm text-red-500 align-middle">{message}</h6>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center gap-2 mb-4 justify-center">
      <div className="flex items-center gap-2">
        <progress
          className="progress progress-primary w-56 mr-2"
          value={progress}
          max="100"
        ></progress>
        <h6 className="text-sm text-gray-500 align-middle">{message}</h6>
      </div>
    </div>
  );
}
