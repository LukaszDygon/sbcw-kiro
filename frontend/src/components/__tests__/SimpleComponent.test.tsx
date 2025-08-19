import React from 'react';
import { render, screen } from '@testing-library/react';
import { AccessibilityProvider } from '../../contexts/AccessibilityContext';

const SimpleComponent: React.FC = () => {
  return <div>Hello World</div>;
};

const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <AccessibilityProvider>
      {children}
    </AccessibilityProvider>
  );
};

describe('Simple Component Test', () => {
  it('renders without crashing', () => {
    render(
      <TestWrapper>
        <SimpleComponent />
      </TestWrapper>
    );

    expect(screen.getByText('Hello World')).toBeInTheDocument();
  });
});