import crypto from 'crypto';
export default function hashId(IP, timestamp, method, path, status) {
    const input = `${IP} + ${timestamp} + ${method} + ${path} + ${status}`;
    const hash = crypto.createHash('sha256').update(input).digest('hex');
    return hash;
}