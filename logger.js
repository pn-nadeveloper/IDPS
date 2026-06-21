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
import express from "express";
import cors from "cors";
import path from "path";
import fs from "fs";
import { fileURLToPath } from 'url';
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();
const logFile = fs.createWriteStream(__dirname + '/logger.log', { flags: 'a' });
const originalLog = console.log;

console.log = function (...args) {
    const time = new Date().toLocaleString('ko-KR', { timeZone: 'Asia/Seoul'});
    const message = args.map(arg =>
        typeof arg === 'string' ? arg : JSON.stringify(arg)
    ).join(' ');

    const logEntry = `${time} ${message}\n`;
    logFile.write(logEntry);
    originalLog.apply(console, [logEntry]);
}
app.use(express.json());
app.use(express.static(__dirname + 'public'));
app.use(cors());

async function insertLogToSupabase(logData, path) {
    const { data, error } = await supabase
        .from('log')
        .insert([logData]);

    if (error) console.error('❌ 전송 에러:', error.message);
    else console.log('✅ Supabase에 로그를 추가했습니다!');
    AI(path, logData.client_ip, logData.log_id, logData);
};

async function updateLogToSupabase(Data, id, logData) {
    const { data, error } = await supabase
        .from('log')
        .update({"proba" : Data.proba, "reason" : Data.reason , "verdict" : Data.status, "ai_source" : Data.source})
        .eq('log_id', id);
    if (error) console.error('❌ 전송 에러:', error.message);
    else {
        console.log('✅ Supabase에 로그를 업데이트했습니다!');
        if (Data.status == "BLOCK" && Data.source == "1st_AI") {
            block_ip(logData.client_ip, Data.reason,id);
        }
        else if (Data.status == "BLOCK" && Data.source == "2nd_AI") {
            warning_ip(id);
        }
    }
}

async function warning_ip(log_id) {
    const { data: logData, error } = await supabase
        .from('log')
        .select('*')
        .eq('log_id', log_id);
    if (error) console.error('❌ 조회 에러:', error.message);
    else {
        const { data, error } = await supabase
        .from('warning')
        .insert(
            {
                log_id: logData[0].log_id,
                timestamp: logData[0].timestamp,
                client_ip: logData[0].client_ip,
                method: logData[0].method,
                path: logData[0].path,
                query_parms : logData[0].query_parms,
                status_code: logData[0].status_code,
                http_size: logData[0].http_size,
                referer: logData[0].referer,
                user_agent: logData[0].user_agent,
                source: logData[0].source,
                check_status: logData[0].check_status,
                proba : logData[0].proba,
                reason : logData[0].reason,
                verdict : logData[0].verdict,
                ai_source : logData[0].ai_source,
                check_status : logData[0].check_status
            }
        )
        if (error) console.error('❌ WARNING 테이블 에러:', error.message);
        else console.log('✅ WARNING 테이블에 로그를 추가했습니다!');
    }
}

async function updateLogToBlockCloudflare(id,log_id) {
    const { data: logData, error } = await supabase
        .from('log')
        .select('*')
        .eq('log_id', log_id);
    if (error) console.error('❌ 조회 에러:', error.message);
    else {
        const { data, error } = await supabase
        .from('block')
        .insert(
            {
                log_id: logData[0].log_id,
                timestamp: logData[0].timestamp,
                client_ip: logData[0].client_ip,
                method: logData[0].method,
                path: logData[0].path,
                query_parms : logData[0].query_parms,
                status_code: logData[0].status_code,
                http_size: logData[0].http_size,
                referer: logData[0].referer,
                user_agent: logData[0].user_agent,
                source: logData[0].source,
                proba : logData[0].proba,
                reason : logData[0].reason,
                verdict : logData[0].verdict,
                ai_source : logData[0].ai_source,
                check_status : "True",
                cloudflare_id: id
            }
        ) 
        if (error) console.error('❌ BLOCK 테이블 에러:', error.message);
        else {
            console.log('✅ BLOCK 테이블에 로그를 추가했습니다!');
            const { data, error } = await supabase
            .from('warning')
            .update({"cloudflare_id": id, "check_status": "True"})
            .eq('log_id', log_id);
            if (error) console.error('❌ WARNING 테이블 에러:', error.message);
            else {console.log('✅ WARNING 테이블에 로그를 업데이트했습니다!');
                const { data, error } = await supabase
                .from('log')
                .update({"cloudflare_id": id , "check_status": "True"})
                .eq('log_id', log_id);
                if (error) console.error('❌ Log 테이블 에러:', error.message);
                else console.log('✅ Log 테이블에 로그를 업데이트했습니다!');
            }
        }
    }
}

async function updateLogToAllowBlockCloudflare(id,log_id) {
    const { data: logData, error } = await supabase
        .from('log')
        .select('*')
        .eq('log_id', log_id);
    if (error) console.error('❌ 조회 에러:', error.message);
    else {
        const { data, error } = await supabase
        .from('block')
        .insert(
            {
                log_id: logData[0].log_id,
                timestamp: logData[0].timestamp,
                client_ip: logData[0].client_ip,
                method: logData[0].method,
                path: logData[0].path,
                query_parms : logData[0].query_parms,
                status_code: logData[0].status_code,
                http_size: logData[0].http_size,
                referer: logData[0].referer,
                user_agent: logData[0].user_agent,
                source: logData[0].source,
                proba : logData[0].proba,
                reason : logData[0].reason,
                verdict : "BLOCK",
                ai_source : logData[0].ai_source,
                check_status : "True",
                cloudflare_id: id
            }
        ) 
        if (error) console.error('❌ BLOCK 테이블 에러:', error.message);
        else {
            console.log('✅ BLOCK 테이블에 로그를 추가했습니다!');
            const { data, error } = await supabase
            .from('log')
            .update({"cloudflare_id": id, "check_status": "True", "verdict": "BLOCK"})
            .eq('log_id', log_id);
            if (error) console.error('❌ Log 테이블 에러:', error.message);
            else console.log('✅ Log 테이블에 로그를 업데이트했습니다!');
        }
    }
}


async function updateLogToCloudflare(id,log_id) {
    const { data: logData, error } = await supabase
        .from('log')
        .select('*')
        .eq('log_id', log_id);
    if (error) console.error('❌ 조회 에러:', error.message);
    else {
        const { data, error } = await supabase
        .from('block')
        .insert(
            {
                log_id: logData[0].log_id,
                timestamp: logData[0].timestamp,
                client_ip: logData[0].client_ip,
                method: logData[0].method,
                path: logData[0].path,
                query_parms : logData[0].query_parms,
                status_code: logData[0].status_code,
                http_size: logData[0].http_size,
                referer: logData[0].referer,
                user_agent: logData[0].user_agent,
                source: logData[0].source,
                check_status: "True",
                proba : logData[0].proba,
                reason : logData[0].reason,
                verdict : "BLOCK",
                ai_source : logData[0].ai_source,
                cloudflare_id: id
            }
        ) 
        if (error) console.error('❌ BLOCK 테이블 에러:', error.message);
        else {
            console.log('✅ BLOCK 테이블에 로그를 추가했습니다!');
            const { data, error } = await supabase
            .from('log')
            .update({"cloudflare_id": id})
            .eq('log_id', log_id);
            if (error) console.error('❌ Log 테이블 에러:', error.message);
            else console.log('✅ Log 테이블에 로그를 업데이트했습니다!');
        }
    }
}

async function updateLogToUnblockCloudflare(log_id) {
    const { data, error } = await supabase
    .from('log')
    .update({"verdict": "ALLOW"})
    .eq('log_id', log_id);
    if (error) console.error('❌ Log 테이블 업데이트 에러:', error.message);
    else{ 
        console.log('✅ Log 테이블에 로그를 업데이트했습니다!');
        const { data, error } = await supabase
        .from('block')
        .delete()
        .eq('log_id', log_id);
        if (error) console.error('❌ BLOCK 테이블 삭제 에러:', error.message);
        else console.log('✅ BLOCK 테이블에 로그를 삭제했습니다!');
    }
}

async function updateLogToPermit(log_id) {
    const { data, error } = await supabase
    .from('log')
    .update({"verdict": "ALLOW"})
    .eq('log_id', log_id);
    if (error) console.error('❌ Log 테이블 업데이트 에러:', error.message);
    else{ 
        console.log('✅ Log 테이블에 로그를 업데이트했습니다!');
        const { data, error } = await supabase
        .from('warning')
        .delete()
        .eq('log_id', log_id);
        if (error) console.error('❌ WARNING 테이블 삭제 에러:', error.message);
        else {
            console.log('✅ WARNING 테이블에 로그를 삭제했습니다!');
            return {"success": true, "message": "허용 성공"};
       }
    }
}

async function updateLogToCheck(log_id) {
    const { data, error } = await supabase
    .from('log')
    .update({"verdict": "ALLOW" , "check_status": "True"})
    .eq('log_id', log_id);
    if (error) console.error('❌ Log 테이블 업데이트 에러:', error.message);
    else{ 
        console.log('✅ Log 테이블에 로그를 업데이트했습니다!');
        return {"success": true, "message": "체크 성공"};
    }
}

async function block_ip(ip, reason,log_id) {
    try{
        const block = await fetch(`http://127.0.0.1:8000/blocked?ip=${ip}&reason=${reason}`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                });
                const block_JSON = await block.json();
                if (block_JSON.status == "success") {
                    //console.log("차단 성공!", block_JSON);
                    const id = block_JSON.message;
                    //console.log(log_id);
                    updateLogToCloudflare(id,log_id);
                } else {
                    console.log("차단 실패!", block_JSON);
                }
    } catch (error) {
        console.log("차단 실패!", error);
    }
}

async function AI(path, ip, id, logData) {
    try{
    const AI = await fetch(`http://127.0.0.1:8000/check?path=${path}&ip=${ip}&id=${id}`, {
                    method: "GET",
                    headers: {
                        "Content-Type": "application/json",
                    },
                });
                const AI_JSON = await AI.json();
                if (AI_JSON.success) {
                    //console.log("AI 정보:", AI_JSON);
                    updateLogToSupabase(AI_JSON, id, logData);
                } else {
                    console.log("AI 에러:", AI_JSON);
                }
} catch (error) {
    console.log("AI 에러:", error);
}
};

app.post('/blocked', async (req, res) => {
    const ip = req.query.ip;
    const reason = req.query.reason;
    const logId = req.query.log_id;
    try {
        const result = await fetch(`http://127.0.0.1:8000/blocked?ip=${ip}&reason=${reason}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
        });
        const result_JSON = await result.json();
        if (result_JSON.status == "success") {
            //console.log("차단 성공!", result_JSON);
            const id = result_JSON.message;
            updateLogToBlockCloudflare(id,logId);
            res.status(200).json({ status: 'success', message: '차단 성공' });
            //console.log("차단 성공!", result_JSON);
            //console.log(logId);
        } else {
            //console.log("차단 실패!", result_JSON);
            res.status(500).json({ status: 'error', message: '차단 실패' });
        }
    } catch (error) {
        console.log('❌ BLOCK 에러:', error);
        res.status(500).json({ status: 'error', message: '차단 실패' });
    }
});

app.post('/allow_blocked', async (req, res) => {
    const ip = req.query.ip;
    const reason = req.query.reason;
    const logId = req.query.log_id;
    try {
        const result = await fetch(`http://127.0.0.1:8000/blocked?ip=${ip}&reason=${reason}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
        });
        const result_JSON = await result.json();
        if (result_JSON.status == "success") {
            //console.log("차단 성공!", result_JSON);
            const id = result_JSON.message;
            updateLogToAllowBlockCloudflare(id,logId);
            res.status(200).json({ status: 'success', message: '차단 성공' });
            //console.log("차단 성공!", result_JSON);
            //console.log(logId);
        } else {
            //console.log("차단 실패!", result_JSON);
            res.status(500).json({ status: 'error', message: '차단 실패' });
        }
    } catch (error) {
        console.log('❌ BLOCK 에러:', error);
        res.status(500).json({ status: 'error', message: '차단 실패' });
    }
});

app.delete('/unblocked', async (req, res) => {
    const id = req.query.id;
    const logId = req.query.log_id;
    try {
        const result = await fetch(`http://127.0.0.1:8000/unblocked?id=${id}`, {
            method: "DELETE",
            headers: {
                "Content-Type": "application/json",
            },
        });
        const result_JSON = await result.json();
        if (result_JSON.status == "success") {
            //console.log("차단 해제 성공!", result_JSON);
            updateLogToUnblockCloudflare(logId);
            res.status(200).json({ status: 'success', message: '차단 해제 성공' });
        } else {
            //console.log("차단 해제 실패!", result_JSON);
            res.status(500).json({ status: 'error', message: '차단 해제 실패' });
        }
    } catch (error) {
        console.log('❌ UNBLOCK 에러:', error);
        res.status(500).json({ status: 'error', message: '차단 해제 실패' });
    }
});

app.put('/permit', async (req, res) => {
    const id = req.query.id;
    try {
        const result = await updateLogToPermit(id);
        if (result.message == "허용 성공") {
            //console.log("허용 성공!", result);
            res.status(200).json({ status: 'success', message: '허용 성공' });
        } else {
            //console.log("허용 실패!", result);
            res.status(500).json({ status: 'error', message: '허용 실패' });
        }
    } catch (error) {
        console.log('❌ 허용 에러:', error);
        res.status(500).json({ status: 'error', message: '허용 실패' });
    }
});

app.put('/check', async (req, res) => {
    const log_id = req.query.id;
    try {
        const result = await updateLogToCheck(log_id);
                if (result.message == "체크 성공") {
                    //console.log("체크 성공!", result);
                    res.status(200).json({ status: 'success', message: '체크 성공' });
                } else {
                    //console.log("체크 실패!", result);
                    res.status(500).json({ status: 'error', message: '체크 실패' });
                }
    } catch (error) {
        console.log('❌ 체크 에러:', error);
        res.status(500).json({ status: 'error', message: '체크 실패' });
    }
});
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
                    source: service.name,
                    check_status: false
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
app.listen(9999, () => console.log('실시간 로그 감시 시작...'));
