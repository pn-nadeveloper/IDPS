export default function agent_null($input) {
    if ($input === '-') {
        return 'unknown agent';
    } else if (!$input) {
        return 'unknown agent';
    } else {
        return $input;
    }
}