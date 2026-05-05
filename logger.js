import parse from './modules/regex_index.mjs';
import { Tail } from 'tail';
import mysql from 'mysql';

// 아파치 로그 파일 경로 (XAMPP 기본 경로 확인)
const logFilePath = 'C:/xampp/apache/logs/access.log';

const tail = new Tail(logFilePath, {
  useWatchFile: true,   // FSWatch 대신 WatchFile 사용 (윈도우에서 더 안정적)
  interval: 1000         // 0.1초마다 파일 체크
});

tail.on("line", function(data) {
    // 여기서 DB INSERT 로직 실행
        const parsedData = parse(data);
        if (parsedData) {
            console.log(`IP: ${parsedData.ip}, Time: ${parsedData.timestamp}, Method: ${parsedData.method}, Path: ${parsedData.path}, Status: ${parsedData.status}, Size: ${parsedData.size}, Referrer: ${parsedData.referrer}, User-Agent: ${parsedData.userAgent}`);
        } else {
            console.log("로그 형식이 예상과 다릅니다:", data);
        }
});

tail.on("error", function(error) {
    console.log('에러 발생:', error);
});

console.log("실시간 로그 감시 시작...");