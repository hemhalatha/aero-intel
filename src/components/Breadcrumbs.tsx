import React from 'react';
import { useLocation, Link } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';

export const Breadcrumbs: React.FC = () => {
  const location = useLocation();
  const pathnames = location.pathname.split('/').filter((x) => x);

  return (
    <div className="flex items-center space-x-2 text-xs font-medium text-slate-500 py-3 px-8 bg-white border-b border-slate-200">
      <Link to="/" className="hover:text-blue-600 flex items-center gap-1.5 transition-colors">
        <Home className="h-3.5 w-3.5 text-slate-400" />
        <span>AeroIntel</span>
      </Link>
      {pathnames.map((name, index) => {
        const routeTo = `/${pathnames.slice(0, index + 1).join('/')}`;
        const isLast = index === pathnames.length - 1;
        const formattedName = name.replace('-', ' ').toUpperCase();

        return (
          <React.Fragment key={name}>
            <ChevronRight className="h-3.5 w-3.5 text-slate-300" />
            {isLast ? (
              <span className="text-slate-900 font-semibold">{formattedName}</span>
            ) : (
              <Link to={routeTo} className="hover:text-blue-600 transition-colors">
                {formattedName}
              </Link>
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
};