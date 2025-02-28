import { mergeClasses } from '../../utils/cn';

export default function Content({
  children,
  className 
}: {
  children: React.ReactNode;
  className?: string;
}) {
  const baseClasses = 'content m-auto w-full max-w-screen-lg';
  return <div className={mergeClasses(baseClasses, className)}>{children}</div>;
}
