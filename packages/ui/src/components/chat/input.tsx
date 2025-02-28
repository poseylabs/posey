import { ChatFormData } from '../../types';
import { Send, Paperclip } from 'lucide-react';
import { Button } from '../form/button';
import { useEffect, useState, useRef } from 'react';

const TaskIndicator: React.FC<{ count: number }> = ({ count }) => (
  <div className="absolute -top-8 left-0 right-0 flex justify-center">
    <div className="flex items-center gap-2 text-sm bg-base-300 px-3 py-1 rounded-full shadow-sm">
      <span className="loading loading-spinner loading-xs"></span>
      <span className="text-base-content/70">
        {count === 1 ? 'Background task in progress...' : `${count} background tasks in progress...`}
      </span>
    </div>
  </div>
);

export interface InputProps extends Omit<React.TextareaHTMLAttributes<HTMLTextAreaElement>, 'onSubmit'> {
  error?: string;
  className?: string;
  disabled?: boolean;
  defaultValue?: string;
  hasActiveTasks?: boolean;
  id?: string;
  label?: string;
  type?: string;
  resetOnSubmit?: boolean;
  placeholder?: string;
  value?: string;
  onSubmit: (data: ChatFormData) => void;
}

export function ChatInput({
  className,
  disabled,
  defaultValue,
  hasActiveTasks,
  id,
  label,
  type = 'text',
  placeholder = "Message Posey",
  resetOnSubmit = true,
  onSubmit,
  value,
  ...props
}: InputProps) {

  const [input, setInput] = useState(defaultValue || '');
  const [attachedFiles, setAttachedFiles] = useState<File[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);


  const submitHandler = (message: string) => {
    onSubmit({
      message: message,
      files: attachedFiles
    });
    setInput('');
    setAttachedFiles([]);
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const maxSize = 10 * 1024 * 1024; // 10MB
      const allowedTypes = [
        'image/jpeg',
        'image/png',
        'image/gif',
        'image/webp',
        'application/pdf',
        'text/plain',
        'text/markdown',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
      ];

      const newFiles = Array.from(e.target.files).filter(file => {
        if (file.size > maxSize) {
          alert(`File ${file.name} is too large. Maximum size is 10MB.`);
          return false;
        }
        if (!allowedTypes.includes(file.type)) {
          alert(`File type ${file.type} is not supported.`);
          return false;
        }
        return true;
      });

      setAttachedFiles(prev => [...prev, ...newFiles]);
    }
  };

  const handleAttachClick = () => {
    fileInputRef.current?.click();
  };

  const removeFile = (index: number) => {
    setAttachedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const _isDisabled = disabled;

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter') {
      if (e.shiftKey) {
        return; // Allow new line with Shift+Enter
      }
      
      if (!_isDisabled) {
        e.preventDefault();
        submitHandler(e.currentTarget.value);
      }
    }
  }

  useEffect(() => {
    if (value && value !== input) {
      setInput(value);
    }
  }, [value]);

  return (
    <div className="flex flex-col gap-2 w-full relative">
      {hasActiveTasks && (
        <TaskIndicator count={1} />
      )}
      
      {attachedFiles.length > 0 && (
        <div className="flex flex-wrap gap-2 p-2 bg-base-300 rounded-lg">
          {attachedFiles.map((file, index) => (
            <div key={index} className="flex items-center gap-2 bg-base-200 p-1 px-2 rounded">
              <span className="text-sm">{file.name}</span>
              <button 
                onClick={() => removeFile(index)}
                className="text-sm hover:text-error"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}
      
      <div className="flex items-end gap-2 w-full border rounded-lg bg-base-200 px-4 py-4">
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          className="hidden"
          multiple
        />
        
        <Button
          className="btn-sm flex-shrink-0"
          onClick={handleAttachClick}
          disabled={_isDisabled || hasActiveTasks}
        >
          <Paperclip className="w-4 h-4" />
        </Button>

        <textarea
          id={id}
          className="grow resize-none bg-transparent border-none focus:outline-none min-h-[28px] max-h-[120px] w-full"
          placeholder={hasActiveTasks ? "Waiting for background tasks to complete..." : placeholder}
          rows={1}
          {...props}
          onKeyDown={handleKeyDown}
          onChange={(e) => {
            setInput(e.target.value);
            e.target.style.height = '28px';
            e.target.style.height = `${Math.min(e.target.scrollHeight, 120)}px`;
          }}
          disabled={_isDisabled || hasActiveTasks}
          value={input}
        />
        
        <Button
          className="btn-sm flex-shrink-0"
          onClick={(e) => {
            e.preventDefault();
            submitHandler(input);
          }}
          disabled={_isDisabled || hasActiveTasks}
        >
          <Send />
        </Button>
      </div>
    </div>
  );
}
