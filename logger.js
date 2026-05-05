import parse from './modules/regex_index.mjs';
import hashId from './modules/hash_id.mjs';
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
            const hash = hashId(parsedData.ip, parsedData.timestamp, parsedData.method, parsedData.path, parsedData.status);
            // parsedData.ip = 원래 IP 주소
            // parsedData.timestamp = 원래 타임스탬프
            // parsedData.method = 원래 메서드
            // parsedData.path = 원래 경로
            // parsedData.status = 원래 상태 코드
            // parsedData.size = 원래 크기
            // parsedData.referrer = 원래 리퍼러
            // parsedData.userAgent = 원래 User-Agent
            // hash = 해시된 ID = primary key로 사용
            console.log(`IP: ${parsedData.ip}, Time: ${parsedData.timestamp}, Method: ${parsedData.method}, Path: ${parsedData.path}, Status: ${parsedData.status}, Size: ${parsedData.size}, Referrer: ${parsedData.referrer}, User-Agent: ${parsedData.userAgent}, Hash ID: ${hash}`);
        } else {
            console.log("로그 형식이 예상과 다릅니다:", data);
        }
});

tail.on("error", function(error) {
    console.log('에러 발생:', error);
});

console.log("실시간 로그 감시 시작...");