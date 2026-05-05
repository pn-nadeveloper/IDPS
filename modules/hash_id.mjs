export default function hashId(IP, timestamp, method, path, status) {
    const input = `${IP} + ${timestamp} + ${method} + ${path} + ${status}`;
    console.log("Hash ID 생성 입력값:", input);
}