export default function source($input) {
    if ($input === 'http://' || $input === 'https://') {
        return 'service1';
    } else if ($input === 'http://' || $input === 'https://') {
        return 'service2';
    } else if ($input === 'http://' || $input === 'https://') {
        return 'service2';
    } else if ($input === 'http://' || $input === 'https://') {
        return 'service1';
    } else {
        return 'error';
    }
}