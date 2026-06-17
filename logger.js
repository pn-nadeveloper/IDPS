import 'dotenv/config';
import { supabase } from './modules/db.mjs';
import parse from './modules/regex_index.mjs';
import hashId from './modules/hash_id.mjs';
import extractQuery from './modules/query_parse.mjs';
import queryToJson from './modules/query_json.mjs';
import decodePath from './modules/path_decode.mjs';
import null_data from './modules/null_data.mjs';
import agent_null from './modules/agent_null.mjs';
import { Tail } from 'tail';
import mysql from 'mysql';
import fetch from 'node-fetch';


async function insertLogToSupabase(logData, path) {
    const { data, error } = await supabase
        .from('log')
        .insert([logData]);

    if (error) console.error('❌ 전송 에러:', error.message);
    else console.log('✅ Supabase에 로그를 추가했습니다!');
    AI(path, logData.client_ip, logData.log_id);
};

async function updateLogToSupabase(Data, id) {
    const { data, error } = await supabase
        .from('log')
        .update({"proba" : Data.proba, "reason" : Data.reason , "verdict" : Data.status, "AI_source" : Data.source})
        .eq('log_id', id);
    if (error) console.error('❌ 전송 에러:', error.message);
    else console.log('✅ Supabase에 로그를 업데이트했습니다!');
}

async function block_ip(ip, reason) {
    try{
        const block = await fetch(`http://127.0.0.1:8000/block?ip=${ip}&reason=${reason}`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                });
                const block_JSON = await block.json();
                if (block_JSON.status == "success") {
                    console.log("차단 성공!", block_JSON);
                } else {
                    console.log("차단 실패!", block_JSON);
                }
    } catch (error) {
        console.log("차단 실패!", error);
    }
}

async function AI(path, ip, id) {
    try{
    const AI = await fetch(`http://127.0.0.1:8000/check?path=${path}&ip=${ip}&id=${id}`, {
                    method: "GET",
                    headers: {
                        "Content-Type": "application/json",
                    },
                });
                const AI_JSON = await AI.json();
                if (AI_JSON.success) {
                    console.log("AI 정보:", AI_JSON);
                    updateLogToSupabase(AI_JSON, id);
                } else {
                    console.log("AI 에러:", AI_JSON);
                }
} catch (error) {
    console.log("AI 에러:", error);
}
};

// 아파치 로그 파일 경로 (XAMPP 기본 경로 확인)
const services = [ { name: 'stellog', path: 'C:/xampp/apache/logs/access.log' },
                  { name: 'stelview', path: 'C:/xampp/apache/logs/stelview-access.log' },
                  { name: 'naver-sso', path: 'C:/xampp/apache/logs/naver-sso-access.log' },
                  //{ name: 'fanding', path: 'C:/xampp/apache/logs/fanding-access.log' },
                  // Example: {name: 'example', path: 'C:/xampp/apache/logs/example.log'},
                ];

services.forEach(service => {
    const tail = new Tail(service.path, {
        useWatchFile: true,
        interval: 1000
    });
    tail.on("line", function(data) {
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
                const logData = {
                    log_id: hash,
                    timestamp: parsedData.timestamp,
                    client_ip: parsedData.ip,
                    method: parsedData.method,
                    path: decodePath(extractQuery(parsedData.path).path),
                    query_parms : queryToJson(extractQuery(parsedData.path).rawQuery),
                    status_code: parsedData.status,
                    http_size: null_data(parsedData.size),
                    referer: null_data(parsedData.referrer),
                    user_agent: agent_null(parsedData.userAgent),
                    // source는 referrer를 기반으로 판단 허나 cloudflare의 경우 x-forwarded-for 헤더로 IP를 전달하기 때문에 
                    // source 판단이 어려움. 일단 referrer 기반으로 판단하되, referrer가 없는 경우는 'unknown'으로 처리 
                    // -> 추후 x-forwarded-for 헤더로 IP를 전달하는 경우 source 판단 로직 추가 필요
                    source: service.name
                    };
                //Promise.all([insertLogToSupabase(logData)]);
                //console.log(`IP: ${parsedData.ip}, Time: ${parsedData.timestamp}, Method: ${parsedData.method}, Path: ${parsedData.path}, Status: ${parsedData.status}, Size: ${parsedData.size}, Referrer: ${parsedData.referrer}, User-Agent: ${parsedData.userAgent}, Hash ID: ${hash}`);
                insertLogToSupabase(logData,parsedData.path);
            } else {
                console.log("로그 형식이 예상과 다릅니다:", data);
            }
    });

    tail.on("error", function(error) {
        console.log('에러 발생:', error);
    });
});
console.log("실시간 로그 감시 시작...");