export const config = {
  matcher: ['/((?!_vercel|_next/static|favicon.ico).*)'],
};

export default async function middleware(request) {
  const expectedUser = process.env.BASIC_AUTH_USER || 'admin';
  const expectedPass = process.env.BASIC_AUTH_PASS;
  const webhookUrl = process.env.DISCORD_WEBHOOK_URL;

  if (!expectedPass) {
    return new Response(
      'Authentication is not configured. Set BASIC_AUTH_PASS env var.',
      { status: 503 }
    );
  }

  const authHeader = request.headers.get('authorization');
  let authenticated = false;

  if (authHeader && authHeader.toLowerCase().startsWith('basic ')) {
    try {
      const encoded = authHeader.substring(6);
      const decoded = atob(encoded);
      const idx = decoded.indexOf(':');
      const user = decoded.substring(0, idx);
      const pass = decoded.substring(idx + 1);
      if (user === expectedUser && pass === expectedPass) {
        authenticated = true;
      }
    } catch (e) {}
  }

  if (!authenticated) {
    return new Response('Authentication required.', {
      status: 401,
      headers: {
        'WWW-Authenticate': 'Basic realm="Portfolio Dashboard", charset="UTF-8"',
        'Content-Type': 'text/plain; charset=utf-8',
      },
    });
  }

  // 認証成功: ページ遷移時のみDiscord通知（サブリソースの読み込みでは通知しない）
  if (webhookUrl) {
    const secFetchDest = request.headers.get('sec-fetch-dest');
    const url = new URL(request.url);
    const isDocument =
      secFetchDest === 'document' ||
      (!secFetchDest && (url.pathname === '/' || url.pathname === '/index.html'));

    if (isDocument) {
      notifyDiscord(webhookUrl, request).catch(() => {});
    }
  }
}

async function notifyDiscord(webhookUrl, request) {
  const rawIp =
    request.headers.get('x-forwarded-for') ||
    request.headers.get('x-real-ip') ||
    'unknown';
  const ip = rawIp.split(',')[0].trim();
  const ua = request.headers.get('user-agent') || 'unknown';
  const country = request.headers.get('x-vercel-ip-country') || '';
  const city = request.headers.get('x-vercel-ip-city') || '';
  const region = request.headers.get('x-vercel-ip-country-region') || '';

  const now = new Date().toLocaleString('ja-JP', {
    timeZone: 'Asia/Tokyo',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });

  const locationParts = [decodeURIComponent(city), region, country].filter(Boolean);
  const location = locationParts.length > 0 ? locationParts.join(', ') : 'unknown';
  const truncatedUa = ua.length > 300 ? ua.substring(0, 300) + '...' : ua;

  const payload = {
    embeds: [
      {
        title: '🔓 Portfolio Dashboard にアクセス',
        color: 0x2563eb,
        fields: [
          { name: '時刻 (JST)', value: now, inline: false },
          { name: 'IP', value: ip, inline: true },
          { name: '位置', value: location, inline: true },
          { name: 'デバイス', value: '```' + truncatedUa + '```', inline: false },
        ],
        timestamp: new Date().toISOString(),
      },
    ],
  };

  await fetch(webhookUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}
