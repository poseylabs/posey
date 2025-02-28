import { mergeClasses } from '../../utils/cn';

export function ContentWrapper({
  children,
  className
}: {
  children: React.ReactNode;
  className?: string;
}) {
  const baseClasses = 'h-full w-full';

  return (
    <div className={mergeClasses(baseClasses, className)}>
      {children}
    </div>
  );
}
