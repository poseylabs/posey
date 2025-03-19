import { forwardRef, useState, useEffect } from 'react';

export interface InputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'onSubmit'> {
  error?: string;
  className?: string;
  defaultValue?: string;
  id?: string;
  label?: string;
  type?: string;
  resetOnSubmit?: boolean;
  placeholder?: string;
  value?: string;
  onChange?: (event: React.ChangeEvent<HTMLInputElement>) => void;
  validate?: (value: string) => Promise<string | undefined>;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, error, id, label, type, onChange, placeholder, validate, value, ...props }, ref) => {
    const [internalValue, setInternalValue] = useState(value || props.defaultValue || '');
    const [validationError, setValidationError] = useState<string | undefined>(undefined);

    // Update internal value when value prop changes
    useEffect(() => {
      if (value !== undefined) {
        setInternalValue(value);
      }
    }, [value]);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = e.target.value;

      // If not controlled externally, update internal state
      if (value === undefined) {
        setInternalValue(newValue);
      }

      // Always call the onChange handler if provided
      if (onChange) {
        onChange(e);
      }
    };

    const handleBlur = async (e: React.FocusEvent<HTMLInputElement>) => {
      // Run validation if provided, but only on blur
      if (validate) {
        const currentValue = value !== undefined ? value : internalValue;
        const result = await validate(currentValue);
        setValidationError(result);
      }

      // Call the onBlur handler if provided
      if (props.onBlur) {
        props.onBlur(e);
      }
    };

    // Determine the final error message (prop takes precedence over validation)
    const errorMessage = error || validationError;

    // Determine if component is controlled or uncontrolled
    const inputValue = value !== undefined ? value : internalValue;

    return (
      <div className="form-control w-full">
        {label && <label htmlFor={id} className="label">
          <span className="label-text">{label}</span>
        </label>}
        <input
          ref={ref}
          id={id}
          type={type}
          placeholder={placeholder}
          className={`${className || 'input input-bordered w-full'} ${errorMessage ? 'input-error' : ''}`}
          value={inputValue}
          onChange={handleChange}
          onBlur={handleBlur}
          {...props}
        />
        {errorMessage && (
          <label className="label">
            <span className="label-text-alt text-error">{errorMessage}</span>
          </label>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
