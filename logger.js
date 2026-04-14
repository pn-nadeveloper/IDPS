const { Tail } = require('tail');
const mysql = require('mysql');

const regex = /^(\S+) \S+ \S+ \[([\w:\/]+\s[+\-]\d{4})\] "(\S+)\s?(\S+)?\s?(\S+)?" (\d{3}) (\d+|-).+? "(.*?)" "(.*?)"$/;

// 아파치 로그 파일 경로 (XAMPP 기본 경로 확인)
const logFilePath = 'C:/xampp/apache/logs/access.log';

const tail = new Tail(logFilePath, {
  useWatchFile: true,   // FSWatch 대신 WatchFile 사용 (윈도우에서 더 안정적)
  interval: 1000         // 0.1초마다 파일 체크
});

tail.on("line", function(data) {
    console.log("새 로그 포착:", data);
    // 여기서 DB INSERT 로직 실행
    const match = data.match(regex);
    if (match) {
        const ip = match[1];
        const timestamp = match[2];
        const method = match[3];
        const path = match[4];
        const protocol = match[5];
        const status = match[6];
        const size = match[7];
        const referrer = match[8];
        const userAgent = match[9];
        console.log(`IP: ${ip}, Time: ${timestamp}, Method: ${method}, Path: ${path}, Status: ${status}, Size: ${size}, Referrer: ${referrer}, User-Agent: ${userAgent}`);
    } else {
        console.log("로그 형식이 예상과 다릅니다:", data);
    }
});

tail.on("error", function(error) {
    console.log('에러 발생:', error);
});

console.log("실시간 로그 감시 시작...");