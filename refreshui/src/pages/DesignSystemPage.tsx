import React, { useState, useEffect } from 'react';
import { Button, Card, Badge, Input } from '../components/ui';
import { Search, Plus, Moon, Sun } from 'lucide-react';

export const DesignSystemPage: React.FC = () => {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  };

  return (
    <div style={{ padding: '40px', maxWidth: '1200px', margin: '0 auto', minHeight: '100vh', transition: 'background-color 0.3s' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '40px' }}>
        <h1>Design System Verification</h1>
        <Button onClick={toggleTheme} variant="secondary" icon={theme === 'light' ? <Moon size={16}/> : <Sun size={16}/>}>
          {theme === 'light' ? 'Dark Mode' : 'Light Mode'}
        </Button>
      </div>
      
      <section style={{ marginBottom: '40px' }}>
        <h2>Typography</h2>
        <div style={{ display: 'grid', gap: '16px' }}>
            <div style={{ fontFamily: 'var(--font-default)' }}>
                <div style={{ fontSize: '12px', color: 'var(--text-tertiary)' }}>Default (Inter)</div>
                <div style={{ fontSize: '18px' }}>The quick brown fox jumps over the lazy dog.</div>
            </div>
            <div style={{ fontFamily: 'var(--font-corporate)' }}>
                <div style={{ fontSize: '12px', color: 'var(--text-tertiary)' }}>Corporate (Roboto)</div>
                <div style={{ fontSize: '18px' }}>The quick brown fox jumps over the lazy dog.</div>
            </div>
            <div style={{ fontFamily: 'var(--font-fun)' }}>
                <div style={{ fontSize: '12px', color: 'var(--text-tertiary)' }}>Fun (Quicksand)</div>
                <div style={{ fontSize: '18px' }}>The quick brown fox jumps over the lazy dog.</div>
            </div>
            <div style={{ fontFamily: 'var(--font-nerd)' }}>
                <div style={{ fontSize: '12px', color: 'var(--text-tertiary)' }}>Nerd (Fira Code)</div>
                <div style={{ fontSize: '18px' }}>The quick brown fox jumps over the lazy dog.</div>
            </div>
            <div style={{ fontFamily: 'var(--font-quirky)' }}>
                <div style={{ fontSize: '12px', color: 'var(--text-tertiary)' }}>Quirky (Space Grotesk)</div>
                <div style={{ fontSize: '18px' }}>The quick brown fox jumps over the lazy dog.</div>
            </div>
        </div>
      </section>

      <section style={{ marginBottom: '40px' }}>
        <h2>Buttons</h2>
        <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
          <Button>Primary Button</Button>
          <Button variant="secondary">Secondary Button</Button>
          <Button variant="ghost">Ghost Button</Button>
          <Button icon={<Plus size={16} />}>With Icon</Button>
        </div>
      </section>

      <section style={{ marginBottom: '40px' }}>
        <h2>Badges</h2>
        <div style={{ display: 'flex', gap: '16px' }}>
          <Badge variant="success">Success</Badge>
          <Badge variant="warning">Warning</Badge>
          <Badge variant="error">Error</Badge>
          <Badge variant="info">Info</Badge>
        </div>
      </section>

      <section style={{ marginBottom: '40px' }}>
        <h2>Inputs</h2>
        <div style={{ maxWidth: '300px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <Input placeholder="Default Input" />
          <Input label="With Label" placeholder="Enter text..." />
          <Input icon={<Search size={16} />} placeholder="With Icon (TODO)" />
        </div>
      </section>

      <section style={{ marginBottom: '40px' }}>
        <h2>Cards</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '24px' }}>
          <Card>
            <h3>Static Card</h3>
            <p>This is a standard glass card.</p>
          </Card>
          <Card interactive>
            <h3>Interactive Card</h3>
            <p>Hover me to see the lift effect.</p>
          </Card>
        </div>
      </section>
    </div>
  );
};
