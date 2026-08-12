import { useEffect, useState } from "react";

export function usePdfObjectUrl(bytes: Uint8Array | null): string | null {
  const [url, setUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!bytes) {
      setUrl(null);
      return;
    }

    const buffer = new Uint8Array(bytes).buffer;
    const nextUrl = URL.createObjectURL(
      new Blob([buffer], { type: "application/pdf" }),
    );
    setUrl(nextUrl);
    return () => URL.revokeObjectURL(nextUrl);
  }, [bytes]);

  return url;
}
