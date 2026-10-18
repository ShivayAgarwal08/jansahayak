import React from 'react';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  elevated?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  elevated = false,
  className = '',
  ...props
}) => {
  return (
    <div
      className={`bg-white rounded-2xl border border-ivory-200 transition-all duration-200 ${
        elevated ? 'shadow-civic-hover hover:border-leaf-200' : 'shadow-civic hover:shadow-civic-hover hover:border-ivory-300'
      } ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};
