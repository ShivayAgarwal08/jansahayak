import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle, ShieldCheck } from 'lucide-react';

interface BadgeProps {
  variant?: 'eligible' | 'possibly_eligible' | 'ineligible' | 'verified' | 'neutral' | 'saffron';
  children: React.ReactNode;
  size?: 'sm' | 'md';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  variant = 'neutral',
  children,
  size = 'md',
  className = '',
}) => {
  const sizeClasses = {
    sm: 'text-xs px-2.5 py-0.5',
    md: 'text-xs px-3 py-1 font-semibold',
  };

  const variantClasses = {
    eligible: 'bg-leaf-50 text-leaf-800 border border-leaf-200',
    possibly_eligible: 'bg-amber-50 text-amber-900 border border-amber-200',
    ineligible: 'bg-red-50 text-red-800 border border-red-200',
    verified: 'bg-blue-50 text-blue-900 border border-blue-200',
    saffron: 'bg-saffron-50 text-saffron-700 border border-saffron-200',
    neutral: 'bg-ivory-100 text-navy-800 border border-ivory-200',
  };

  const getIcon = () => {
    switch (variant) {
      case 'eligible':
        return <CheckCircle2 className="w-3.5 h-3.5 text-leaf-600" />;
      case 'possibly_eligible':
        return <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />;
      case 'ineligible':
        return <XCircle className="w-3.5 h-3.5 text-red-600" />;
      case 'verified':
        return <ShieldCheck className="w-3.5 h-3.5 text-blue-600" />;
      default:
        return null;
    }
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full ${sizeClasses[size]} ${variantClasses[variant]} ${className}`}
    >
      {getIcon()}
      <span>{children}</span>
    </span>
  );
};
