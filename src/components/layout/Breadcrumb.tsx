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
    <nav className="flex items-center space-x-1.5 text-xs text-[#9CA3AF] mb-5">
      <Link
        to="/dashboard"
        className="flex items-center gap-1 text-[#6B7280] dark:text-[#9CA3AF] hover:text-[#1F2937] dark:hover:text-[#F3F4F6] transition-colors font-medium"
      >
        <Home className="w-3.5 h-3.5 text-[#9CA3AF]" />
        <span>ChronaNexus</span>
      </Link>

      {pathnames.map((value, index) => {
        const to = `/${pathnames.slice(0, index + 1).join('/')}`;
        const isLast = index === pathnames.length - 1;

        return (
          <React.Fragment key={to}>
            <ChevronRight className="w-3.5 h-3.5 text-[#9CA3AF]" />
            {isLast ? (
              <span className="font-semibold text-[#1F2937] dark:text-[#F3F4F6]">
                {formatPath(value)}
              </span>
            ) : (
              <Link
                to={to}
                className="text-[#6B7280] dark:text-[#9CA3AF] hover:text-[#1F2937] dark:hover:text-[#F3F4F6] transition-colors"
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
