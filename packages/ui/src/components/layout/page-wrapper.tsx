export function PageWrapper({
  children
}: {
  children: React.ReactNode;
}) {
  return <div className="page-wrapper flex flex-col h-screen">{children}</div>;
}
