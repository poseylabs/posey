import { mergeClasses } from '../../utils/cn';

export interface AvatarProps extends React.HTMLAttributes<HTMLDivElement> {
  src?: string | null;
  alt?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const sizeClasses = {
  sm: 'w-8 h-8',
  md: 'w-10 h-10',
  lg: 'w-16 h-16'
};

export function Avatar({ 
  src, 
  alt = '', 
  size = 'md',
  className,
  ...props 
}: AvatarProps) {
  return (
    <div className={mergeClasses("avatar", className)} {...props}>
      <div className={mergeClasses("rounded-full", sizeClasses[size])}>
        {src ? (
          <img
            src={src}
            alt={alt}
            className="object-cover"
          />
        ) : (
          <div className="bg-neutral-focus flex items-center justify-center text-neutral-content">
            {alt ? alt.charAt(0).toUpperCase() : '?'}
          </div>
        )}
      </div>
    </div>
  );
} 
