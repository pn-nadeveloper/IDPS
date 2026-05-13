export default function parseLogLine(logLine) {

const regex = /^([0-9a-fA-F:.]+) \S+ \S+ \[([\w:\/]+\s[+\-]\d{4})\] "(\S+)\s?(\S+)?\s?(\S+)?" (\d{3}) (\d+|-) "(.*?)" "(.*?)"$/;

    const match = logLine.match(regex);
    if (match) {
        return {
            ip: match[1],
            timestamp: match[2],
            method: match[3],
            path: match[4],
            protocol: match[5],
            status: match[6],
            size: match[7],
            referrer: match[8],
            userAgent: match[9]
        };
    }
    return null;
}