import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MainLayout } from './MainLayout';

describe('MainLayout', () => {
  it('renders children in content area', () => {
    render(
      <MainLayout showHeader={false}>
        <div data-testid="content">Main Content</div>
      </MainLayout>
    );

    expect(screen.getByTestId('content')).toBeInTheDocument();
    expect(screen.getByText('Main Content')).toBeInTheDocument();
  });

  it('renders header when showHeader is true', () => {
    render(
      <MainLayout showHeader header={<div data-testid="header">Header Content</div>}>
        <div>Content</div>
      </MainLayout>
    );

    expect(screen.getByTestId('header')).toBeInTheDocument();
    expect(screen.getByText('Header Content')).toBeInTheDocument();
  });

  it('does not render header when showHeader is false', () => {
    render(
      <MainLayout showHeader={false} header={<div data-testid="header">Header</div>}>
        <div>Content</div>
      </MainLayout>
    );

    expect(screen.queryByTestId('header')).not.toBeInTheDocument();
  });

  it('renders sidebar when provided', () => {
    render(
      <MainLayout
        showHeader={false}
        sidebar={<div data-testid="sidebar">Sidebar Content</div>}
      >
        <div>Content</div>
      </MainLayout>
    );

    expect(screen.getByTestId('sidebar')).toBeInTheDocument();
    expect(screen.getByText('Sidebar Content')).toBeInTheDocument();
  });

  it('does not render sidebar when not provided', () => {
    const { container } = render(
      <MainLayout showHeader={false}>
        <div>Content</div>
      </MainLayout>
    );

    expect(container.querySelector('aside')).not.toBeInTheDocument();
  });

  it('applies custom className to container', () => {
    const { container } = render(
      <MainLayout showHeader={false} className="custom-container">
        <div>Content</div>
      </MainLayout>
    );

    expect(container.firstChild).toHaveClass('custom-container');
  });

  it('applies custom className to content area', () => {
    const { container } = render(
      <MainLayout showHeader={false} contentClassName="custom-content">
        <div>Content</div>
      </MainLayout>
    );

    const main = container.querySelector('main');
    expect(main).toHaveClass('custom-content');
  });

  it('applies custom className to sidebar', () => {
    const { container } = render(
      <MainLayout
        showHeader={false}
        sidebar={<div>Sidebar</div>}
        sidebarClassName="custom-sidebar"
      >
        <div>Content</div>
      </MainLayout>
    );

    const aside = container.querySelector('aside');
    expect(aside).toHaveClass('custom-sidebar');
  });

  it('applies custom className to header', () => {
    const { container } = render(
      <MainLayout
        showHeader
        header={<div>Header</div>}
        headerClassName="custom-header"
      >
        <div>Content</div>
      </MainLayout>
    );

    const header = container.querySelector('header');
    expect(header).toHaveClass('custom-header');
  });

  it('renders all three regions together', () => {
    const { container } = render(
      <MainLayout
        showHeader
        header={<div data-testid="header">Header</div>}
        sidebar={<div data-testid="sidebar">Sidebar</div>}
      >
        <div data-testid="content">Content</div>
      </MainLayout>
    );

    expect(screen.getByTestId('header')).toBeInTheDocument();
    expect(screen.getByTestId('sidebar')).toBeInTheDocument();
    expect(screen.getByTestId('content')).toBeInTheDocument();
    expect(container.querySelector('header')).toBeInTheDocument();
    expect(container.querySelector('aside')).toBeInTheDocument();
    expect(container.querySelector('main')).toBeInTheDocument();
  });

  it('applies collapsed class to sidebar when sidebarCollapsed is true', () => {
    const { container } = render(
      <MainLayout
        showHeader={false}
        sidebar={<div>Sidebar</div>}
        sidebarCollapsed
      >
        <div>Content</div>
      </MainLayout>
    );

    const aside = container.querySelector('aside');
    // CSS modules hash class names, so check if class contains 'collapsed'
    expect(aside?.className).toMatch(/collapsed/);
  });

  it('applies sidebarRight class when sidebarPosition is right', () => {
    const { container } = render(
      <MainLayout
        showHeader={false}
        sidebar={<div>Sidebar</div>}
        sidebarPosition="right"
      >
        <div>Content</div>
      </MainLayout>
    );

    // CSS modules hash class names, so check if class contains 'sidebarRight'
    expect((container.firstChild as HTMLElement)?.className).toMatch(/sidebarRight/);
  });

  it('defaults showHeader to true', () => {
    const { container } = render(
      <MainLayout header={<div>Header</div>}>
        <div>Content</div>
      </MainLayout>
    );

    expect(container.querySelector('header')).toBeInTheDocument();
  });
});
