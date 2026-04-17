export const config = {
  matcher: ['/((?!_vercel|_next/static|favicon.ico).*)'],
};

export default function middleware(request) {
  const expectedUser = process.env.BASIC_AUTH_USER || 'admin';
  const expectedPass = process.env.BASIC_AUTH_PASS;

  if (!expectedPass) {
    return new Response(
      'Authentication is not configured. Set BASIC_AUTH_PASS env var.',
      { status: 503 }
    );
  }

  const authHeader = request.headers.get('authorization');
  if (authHeader && authHeader.toLowerCase().startsWith('basic ')) {
    try {
      const encoded = authHeader.substring(6);
      const decoded = atob(encoded);
      const idx = decoded.indexOf(':');
      const user = decoded.substring(0, idx);
      const pass = decoded.substring(idx + 1);
      if (user === expectedUser && pass === expectedPass) {
        return;
      }
    } catch (e) {}
  }

  return new Response('Authentication required.', {
    status: 401,
    headers: {
      'WWW-Authenticate': 'Basic realm="Portfolio Dashboard", charset="UTF-8"',
      'Content-Type': 'text/plain; charset=utf-8',
    },
  });
}
