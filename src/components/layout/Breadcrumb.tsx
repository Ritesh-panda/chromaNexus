import React from 'react';
import { useLocation, Link } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';

export const Breadcrumb: React.FC = () => {
  const location = useLocation();
  const pathnames = location.pathname.split('/').filter((x) => x);

  const formatPath = (name: string) => {
    return name
      .replace(/-/g, ' ')
      .replace(/\b\w/g, (l) => l.toUpperCase());
  };

  return (
    <nav className="flex items-center space-x-2 text-xs text-slate-400 mb-6">
      <Link
        to="/dashboard"
        className="flex items-center gap-1 hover:text-slate-700 dark:hover:text-slate-200 transition-colors font-medium"
      >
        <Home className="w-3.5 h-3.5" />
        <span>ChronaNexus</span>
      </Link>

      {pathnames.map((value, index) => {
        const to = `/${pathnames.slice(0, index + 1).join('/')}`;
        const isLast = index === pathnames.length - 1;

        return (
          <React.Fragment key={to}>
            <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
            {isLast ? (
              <span className="font-semibold text-blue-600 dark:text-blue-400">
                {formatPath(value)}
              </span>
            ) : (
              <Link
                to={to}
                className="hover:text-slate-700 dark:hover:text-slate-200 transition-colors"
              >
                {formatPath(value)}
              </Link>
            )}
          </React.Fragment>
        );
      })}
    </nav>
  );
};
