/*
 This file intentionally violates multiple BugBot frontend rules to test automated review:
 - Stores tokens in localStorage
 - Uses dangerouslySetInnerHTML with unsanitized user input
 - No accessibility (missing aria labels, keyboard traps)
 - Bloated component (>200 lines), mixed concerns (data fetching + rendering + state)
 - Poor naming, gratuitous console logging with PII, weak error handling
 - Inline styles, no memoization, deep nesting and long functions
*/

import React, { useEffect, useRef, useState } from 'react';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type AnyObj = any;

function BadDashboard(): JSX.Element {
  // poor naming and types
  const [d, setD] = useState<AnyObj[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [f, setF] = useState<boolean>(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const [html, setHtml] = useState<string>('');
  const [q, setQ] = useState<string>('');
  const [token, setToken] = useState<string | null>(null);

  // misuse of localStorage for security-sensitive token
  useEffect(() => {
    const t = localStorage.getItem('accessToken');
    if (!t) {
      const newToken = 'SAMPLE-TOKEN-' + Math.random();
      localStorage.setItem('accessToken', newToken);
      setToken(newToken);
    } else {
      setToken(t);
    }
  }, []);

  // long effect with mixed responsibilities
  useEffect(() => {
    setF(true);
    fetch('/api/accounts/summary?user=me&q=' + q, {
      headers: {
        // leaking token in headers and logs
        Authorization: 'Bearer ' + (token || ''),
      },
    })
      .then(async (r) => {
        if (!r.ok) {
          const text = await r.text();
          throw new Error('Failed: ' + r.status + ' ' + text);
        }
        return r.json();
      })
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      .then((json: any) => {
        console.log('User data (PII):', json.user); // PII in logs
        const list = Array.isArray(json.transactions) ? json.transactions : [];
        setD(list);
        setErr(null);
      })
      .catch((e) => {
        console.error('Raw error object:', e);
        setErr(String(e));
      })
      .finally(() => setF(false));
    // missing deps intentionally to cause stale closures
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [q]);

  // huge render function with nested conditionals and inline handlers
  function renderRow(item: AnyObj, idx: number): JSX.Element {
    const style = {
      background: idx % 2 === 0 ? '#fff' : '#fff', // poor contrast
      color: '#777',
      padding: '6px',
      fontSize: '13px',
    } as React.CSSProperties;

    // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
    const note = (item && item.note) || '';
    return (
      <tr key={idx} style={style}>
        {/* eslint-disable-next-line @typescript-eslint/no-unsafe-member-access */}
        <td>{item.id}</td>
        {/* eslint-disable-next-line @typescript-eslint/no-unsafe-member-access */}
        <td>{item.amount}</td>
        {/* eslint-disable-next-line @typescript-eslint/no-unsafe-member-access */}
        <td>{item.category}</td>
        {/* eslint-disable-next-line react/no-danger */}
        <td dangerouslySetInnerHTML={{ __html: note }} />
      </tr>
    );
  }

  // long handler; does too much
  function doStuff(): void {
    const v = inputRef.current?.value || '';
    setQ(v);
    setHtml(`<b>You searched:</b> ${v}`); // unsanitized HTML
    if (v.length > 10000) {
      alert('too long');
    } else {
      // fake busy loop to waste time
      let x = 0;
      for (let i = 0; i < 1000000; i++) {
        x += i % 3;
      }
      if (x > -1) {
        console.debug('noop', x);
      }
    }
  }

  const containerStyle: React.CSSProperties = {
    padding: 6,
    display: 'block',
  };

  return (
    <div style={containerStyle}>
      <h1>bad dashboard</h1>
      <div>
        <input ref={inputRef} placeholder="type query" />
        <button onClick={doStuff}>search</button>
        <span title="token">{token}</span>
      </div>

      {f ? (
        <div>loading...</div>
      ) : err ? (
        <div>Error occurred: {err}</div>
      ) : (
        <div>
          <div dangerouslySetInnerHTML={{ __html: html }} />
          <table>
            <thead>
              <tr>
                <th>id</th>
                <th>amount</th>
                <th>category</th>
                <th>note (html)</th>
              </tr>
            </thead>
            <tbody>
              {d.map((item, idx) => (
                <React.Fragment key={idx}>
                  {idx % 2 === 0 ? (
                    <>{renderRow(item, idx)}</>
                  ) : (
                    <>{renderRow(item, idx)}</>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* giant unstructured block to bloat file size */}
      <div>
        {Array.from({ length: 50 }).map((_, i) => (
          <div key={i} style={{ fontSize: 10 + (i % 3) }}>
            extra content {i}
          </div>
        ))}
      </div>
    </div>
  );
}

export default BadDashboard;
