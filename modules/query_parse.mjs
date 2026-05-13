export default function extractQuery(fullPath) {
    if (!fullPath) return { path: '', rawQuery: '' };
    
    const [path, ...queryParts] = fullPath.split('?');
    return {
        path: path,
        rawQuery: queryParts.join('?')
    };
}