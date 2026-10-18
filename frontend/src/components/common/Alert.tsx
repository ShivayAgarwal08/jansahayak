import React from 'react';
import { Info, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';

interface AlertProps {
  type?: 'info' | 'warning' | 'success' | 'error';
  title?: string;
  children: React.ReactNode;
  className?: string;
}

export const Alert: React.FC<AlertProps> = ({
  type = 'info',
  title,
  children,
  className = '',
}) => {
  const styles = {
    info: {
      bg: 'bg-softsky/50 border-blue-200 text-navy-900',
      icon: <Info className="w-5 h-5 text-blue-700 shrink-0" />,
    },
    warning: {
      bg: 'bg-amber-50 border-amber-200 text-amber-950',
      icon: <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0" />,
    },
    success: {
      bg: 'bg-softmint border-leaf-200 text-leaf-950',
      icon: <CheckCircle className="w-5 h-5 text-leaf-700 shrink-0" />,
    },
    error: {
      bg: 'bg-red-50 border-red-200 text-red-950',
      icon: <XCircle className="w-5 h-5 text-red-600 shrink-0" />,
    },
  };

  const current = styles[type];

  return (
    <div className={`p-4 rounded-xl border flex gap-3 text-sm ${current.bg} ${className}`}>
      {current.icon}
      <div className="space-y-1">
        {title && <h5 className="font-semibold text-sm">{title}</h5>}
        <div className="text-sm opacity-90 leading-relaxed">{children}</div>
      </div>
    </div>
  );
};
