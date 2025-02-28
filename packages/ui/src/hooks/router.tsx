import React, { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useRouter as useNextRouter } from 'next/navigation';

export const usePoseyRouter = ({ useHashLinks = false }: {
  useHashLinks?: boolean;
}) => {
  // Try to get Next.js router first
  let nextRouter: any;
  try {
    nextRouter = useNextRouter();
  } catch (e) {
    // Next.js router not available
  }

  // Try to get React Router navigate function
  let reactNavigate: any;
  try {
    reactNavigate = useNavigate();
  } catch (e) {
    // React Router not available
  }

  const linkTo = useCallback((href: string) => {
    const path = useHashLinks ? href.replace(/^\//, '') : href;

    if (!useHashLinks && nextRouter) {
      console.log('Navigating with next-router', path);
      nextRouter.push(path);
    } else if (useHashLinks && reactNavigate) {
      console.log('Navigating with react-router', path);
      reactNavigate(path, { replace: true });
    } else {
      console.warn('No router available - falling back to window.location');
      window.location.href = path;
    }
  }, [nextRouter, reactNavigate, useHashLinks]);

  const Link = ({ href, className, children }: { href: string, className?: string, children: React.ReactNode }) => {
    return (
      <a href={href} onClick={() => linkTo(href)} className={className}>{children}</a> 
    );
  };

  return {
    linkTo,
    Link
  };
};
