var USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36(KHTML, like Gecko)';
var GOOG_API_KEY = 'AIzaSyDyT5W0Jh49F30Pqqtyfdf7pDLFKLJoAnw';
var REQUEST_KEY = 'O43z0dpjhgX20SCx4KAo';
var YT_BASE_URL = 'https://www.youtube.com';
var GOOG_BASE_URL = 'https://jnn-pa.googleapis.com';

var globalObj = (typeof globalThis !== 'undefined') ? globalThis :
    (typeof global !== 'undefined') ? global :
        (typeof window !== 'undefined') ? window :
            (typeof self !== 'undefined') ? self :
                this;

if ((typeof process !== 'undefined') &&
    (typeof process.versions.node !== 'undefined')) {
    var jsdom = require('jsdom');
    var dom = new jsdom.JSDOM();
    Object.assign(globalObj, {
        window: dom.window,
        document: dom.window.document
    });
}

function exit(code) {
    if (typeof phantom !== 'undefined') {
        // phantom.exit();
        phantom.exit(code);
        // yt-dlp's PhantomJSwrapper relies on
        // `'phantom.exit();' in jscode`
    } else if (typeof process !== 'undefined')
        process.exit(code);
}

function compatGetProcessArgs() {
    if (typeof process !== 'undefined' && typeof process.argv !== 'undefined') {
        if (process.argv.length <= 2) return [];
        var args = process.argv.slice(2);
        return args;
    } else if (typeof phantom !== 'undefined') {
        var system = require('system');
        if (system.args.length <= 1) return [];
        var args = system.args.slice(1);
        return args;
    } else {
        console.error('Unknown environment!');
    }
}

function compatFetch(resolve, reject, url, req) {
    function splitHeaders(headers) {
        var headersMod = {};
        var userAgent;
        for (var key in headers) {
            if (key.toLowerCase() === 'user-agent') {
                userAgent = headers[key];
                delete headers[key];
            } else {
                headersMod[key] = headers[key];
            }
        }
        return {
            headers: headersMod,
            userAgent: userAgent
        };
    }
    function doXHR(args) {
        xhr = new XMLHttpRequest();
        xhr.open(args.req.method, args.url, true);
        for (var hdr in args.req.headers)
            xhr.setRequestHeader(hdr, args.req.headers[hdr]);
        var doneCallbacks = [];
        xhr.onreadystatechange = function () {
            if (xhr.readyState === 2) {
                args.resolve({
                    ok: (xhr.status >= 200 && xhr.status < 300),
                    status: xhr.status,
                    url: xhr.responseUrl,
                    text: function (resolveInner, rejectInner) {
                        doneCallbacks.push(resolveInner);
                    },
                    json: function (resolveInner, rejectInner) {
                        doneCallbacks.push(function (responseText) {
                            var parsed;
                            try {
                                parsed = JSON.parse(responseText);
                            } catch (err) {
                                return rejectInner(err);
                            }
                            resolveInner(parsed);
                        });
                    },
                    headers: {
                        get: function (name) {
                            return xhr.getResponseHeader(name);
                        },
                        _raw: xhr.getAllResponseHeaders()
                    }
                });
            } else if (xhr.readyState === 4) {
                doneCallbacks = doneCallbacks.filter(function (x) {
                    if (x)
                        x(xhr.responseText);
                    return false;
                });
            }
        };
        xhr.onerror = function () {
            args.reject(new Error('XHR failed'));
        };

        if (args.req && typeof args.req.timeout === 'number') {
            xhr.timeout = args.req.timeout;
        }

        xhr.ontimeout = function () {
            args.reject(new Error('XHR timed out'));
        };

        try {
            xhr.send(args.req.body);
        } catch (err) {
            args.reject(err);
        }
    }
    req = req || {};
    req.method = req.method ? req.method.toUpperCase() : (req.body ? 'POST' : 'GET');
    req.headers = req.headers || {};
    req.body = req.body || null;
    req.useXHR = req.useXHR || false;
    var splitHeadersResult = splitHeaders(req.headers);
    if (splitHeadersResult.userAgent && typeof phantom !== 'undefined') {
        doXHR({ resolve: resolve, reject: reject, url: url, req: req });
    } else if (typeof fetch === 'function') {
        fetch(url, req).then(function (response) {
            return {
                ok: response.ok,
                status: response.status,
                url: response.url,
                text: function (resolveInner, rejectInner) {
                    response.text().then(resolveInner).catch(rejectInner);
                },
                json: function (resolveInner, rejectInner) {
                    response.json().then(resolveInner).catch(rejectInner);
                },
                headers: {
                    get: response.headers.get,
                    _raw: response.headers
                }
            };
        }).then(resolve).catch(reject);
    } else if (typeof XMLHttpRequest !== 'undefined' && (!splitHeadersResult.userAgent || req.useXHR)) {
        doXHR({ resolve: resolve, reject: reject, url: url, req: req });
    } else {
        reject(new Error('Could not find available networking API.'));
    }
}

function buildURL(endpointName, useYouTubeAPI) {
    return ''.concat(
        useYouTubeAPI ? YT_BASE_URL : GOOG_BASE_URL, '/',
        useYouTubeAPI ? 'api/jnn/v1' : '$rpc/google.internal.waa.v1.Waa',
        '/', endpointName);
}

var base64urlToBase64Map = {
    '-': '+',
    _: '/',
    '.': '='
};

var base64urlCharRegex = /[-_.]/g;

function b64ToUTF8Arr(b64) {
    var b64Mod;

    if (base64urlCharRegex.test(b64)) {
        b64Mod = base64.replace(base64urlCharRegex, function (match) {
            return base64urlToBase64Map[match];
        });
    } else {
        b64Mod = b64;
    }
    var b64Mod = atob(b64Mod);
    var ret = [];
    b64Mod.split('').forEach(function (chr) {
        ret.push(chr.charCodeAt(0));
    });
    return ret;
}

function decodeUTF8Arr(array) {
    var out = '';
    array.forEach(function (byte) {
        out += '%' + ('0' + byte.toString(16)).slice(-2)
    });
    return decodeURIComponent(out);
}

function UTF8ArrToB64(u8, b64Url) {
    b64Url = (typeof b64Url === 'undefined') ? false : b64Url;
    var str = '';
    Array.prototype.forEach.call(u8, function (chrCode) {
        str += String.fromCharCode(chrCode);
    });
    var result = btoa(str);
    if (b64Url) {
        return result
            .replace(/\+/g, '-')
            .replace(/\//g, '_');
    }
    return result;
}

// We need UTF 8
function encodeASCII(str) {
    var ret = [];
    str.split('').forEach(function (chr) {
        ret.push(chr.charCodeAt(0));
    });
    return ret;
}

function descramble(scrambledChallenge) {
    var buf = b64ToUTF8Arr(scrambledChallenge);
    return decodeUTF8Arr(buf.map(function (chr) {
        return chr + 97;
    }));;
}

function parseChallengeData(rawData) {
    var challengeData = [];
    if (rawData.length > 1 && typeof rawData[1] === 'string') {
        var descrambled = descramble(rawData[1]);
        challengeData = JSON.parse(descrambled || '[]');
    } else if (rawData.length && typeof rawData[0] === 'object') {
        challengeData = rawData[0];
    }
    var wrappedScript = challengeData[1];
    var wrappedUrl = challengeData[2];
    function arrFind(arr, fn) {
        if (typeof Array.prototype.find === 'function')
            return arr.find(fn);
        for (var i = 0; i < arr.length; ++i)
            if (fn(arr[i], i, arr)) return arr[i];
    }
    function found(value) {
        return value && typeof value === 'string';
    }
    var privateDoNotAccessOrElseSafeScriptWrappedValue = Array.isArray(wrappedScript) ?
        arrFind(wrappedScript, found) : null;
    var privateDoNotAccessOrElseTrustedResourceUrlWrappedValue = Array.isArray(wrappedUrl) ?
        arrFind(wrappedUrl, found) : null;
    return {
        messageId: challengeData[0],
        interpreterJavascript: {
            privateDoNotAccessOrElseSafeScriptWrappedValue: privateDoNotAccessOrElseSafeScriptWrappedValue,
            privateDoNotAccessOrElseTrustedResourceUrlWrappedValue: privateDoNotAccessOrElseTrustedResourceUrlWrappedValue
        },
        interpreterHash: challengeData[3],
        program: challengeData[4],
        globalName: challengeData[5],
        clientExperimentsStateBlob: challengeData[7],
    }
}

function load(resolve, reject, vm, program, userInteractionElement) {
    if (!vm)
        reject(new Error('VM not found'));
    if (!vm.a)
        reject(new Error('VM init function not found'));
    var vmFns;
    var asyncResolved = false;
    var syncResolved = false;
    var syncSnapshotFunction;
    function maybeDone() {
        if (asyncResolved && syncResolved) {
            resolve({
                syncSnapshotFunction: syncSnapshotFunction,
                vmFns: vmFns,
            });
        }
    }
    function vmFunctionsCallback(asyncSnapshotFunction, shutdownFunction, passEventFunction, checkCameraFunction) {
        vmFns = {
            asyncSnapshotFunction: asyncSnapshotFunction,
            shutdownFunction: shutdownFunction,
            passEventFunction: passEventFunction,
            checkCameraFunction: checkCameraFunction
        };
        asyncResolved = true;
        maybeDone();
    }
    syncSnapshotFunction = vm.a(program, vmFunctionsCallback, true, userInteractionElement, function () { }, [[], []])[0];
    syncResolved = true;
    maybeDone();
}

function snapshot(resolve, reject, vmFns, args, timeout) {
    timeout = (typeof timeout === 'undefined') ? 3000 : timeout;
    var timeoutId;
    function resolveWrapped(x) {
        clearTimeout(timeoutId);
        resolve(x);
    }
    function rejectWrapped(x) {
        clearTimeout(timeoutId);
        reject(x);
    }
    timeoutId = setTimeout(function () {
        reject(new Error('VM operation timed out'));
    }, timeout);
    if (!vmFns.asyncSnapshotFunction)
        return rejectWrapped(new Error('Asynchronous snapshot function not found'));
    vmFns.asyncSnapshotFunction(function (response) { resolveWrapped(response) }, [
        args.contentBinding,
        args.signedTimestamp,
        args.webPoSignalOutput,
        args.skipPrivacyBuffer
    ]);
}

function getWebSafeMinter(resolve, reject, integrityTokenData, webPoSignalOutput) {
    var getMinter = webPoSignalOutput[0];
    if (!getMinter)
        reject(new Error('PMD:Undefined'));
    if (!integrityTokenData.integrityToken)
        reject(new Error('No integrity token provided'));
    var mintCallback = getMinter(b64ToUTF8Arr(integrityTokenData.integrityToken));
    if (typeof mintCallback !== 'function')
        reject(new Error('APF:Failed'));
    resolve(function (resolveInner, rejectInner, identifier) {
        var result = mintCallback(encodeASCII(identifier));
        if (!result)
            rejectInner(new Error('YNJ:Undefined'));
        // do we need to test if result is a U8arr?
        resolveInner(UTF8ArrToB64(result, true));
    });
}

function isBrowser() {
    var isBrowser = typeof window !== 'undefined'
        && typeof window.document !== 'undefined'
        && typeof window.document.createElement !== 'undefined'
        && typeof window.HTMLElement !== 'undefined'
        && typeof window.navigator !== 'undefined'
        && typeof window.getComputedStyle === 'function'
        && typeof window.requestAnimationFrame === 'function'
        && typeof window.matchMedia === 'function';

    var hasValidWindow = false;
    var windowObj = Object.getOwnPropertyDescriptor(globalObj, 'window');
    if (windowObj && windowObj.get && typeof windowObj.get.toString == 'function') {
        var str = windowObj.get.toString();
        hasValidWindow = str.indexOf('[native code]') !== -1;
    }

    return isBrowser && hasValidWindow;
}

(function () {
    var headers = {
        'Content-Type': 'application/json+protobuf',
        'X-Goog-Api-Key': GOOG_API_KEY,
        'X-User-Agent': 'grpc-web-javascript/0.1'
    }
    if (!isBrowser())
        headers['User-Agent'] = USER_AGENT;

    var identifiers = compatGetProcessArgs();
    if (!identifiers.length) {
        console.warn('No identifiers provided! Pass them as CLI arguments.');
        console.log('[]');
        exit(0);
    }
    var fetchChallengePayload = [REQUEST_KEY];
    compatFetch(function (x) {
        if (!x.ok) {
            console.error('Failed to fetch challenge');
            exit(1);
        }
        x.json(function (rawDataJson) {
            var bgChallenge = parseChallengeData(rawDataJson);
            if (!bgChallenge) {
                console.error(new Error('Could not get challenge'));
                exit(1);
            }

            var interpreterJavascript = bgChallenge.interpreterJavascript.privateDoNotAccessOrElseSafeScriptWrappedValue;
            if (interpreterJavascript) {
                new Function(interpreterJavascript)();
            } else {
                console.error('Could not load VM');
                exit(1);
            }

            load(
                function (bg) {
                    var webPoSignalOutput = [];
                    snapshot(function (botguardResponse) {
                        var generatePayload = [REQUEST_KEY, botguardResponse];
                        compatFetch(function (integrityTokenResponse) {
                            integrityTokenResponse.json(function (integrityTokenJson) {
                                var integrityTokenData = {
                                    integrityToken: integrityTokenJson[0],
                                    estimatedTtlSecs: integrityTokenJson[1],
                                    mintRefreshThreshold: integrityTokenJson[2],
                                    websafeFallbackToken: integrityTokenJson[3]
                                }
                                getWebSafeMinter(function (webSafeMinter) {
                                    var pots = [];
                                    function exitIfCompleted() {
                                        if (Object.keys(pots).length == identifiers.length) {
                                            console.log(JSON.stringify(pots));
                                            exit(+(pots.indexOf(null) !== -1));
                                        }
                                    }
                                    identifiers.forEach(function (identifier, idx) {
                                        webSafeMinter(function (pot) {
                                            pots[idx] = pot;
                                            exitIfCompleted();
                                        }, function (err) {
                                            console.error(
                                                'Failed to mint web-safe POT for identifier'.concat(identifier, ':'), err);
                                            pots[idx] = null;
                                            exitIfCompleted();
                                        }, identifier);
                                    });
                                }, function (err) {
                                    console.error('Failed to get web-safe minter:', err);
                                    exit(1);
                                }, integrityTokenData, webPoSignalOutput);
                            }, function (err) {
                                console.error('Failed to parse JSON:', err);
                                exit(1);
                            });
                        }, function (err) {
                            console.error('Failed to fetch integrity token response:', err);
                            exit(1);
                        }, buildURL('GenerateIT', false), {
                            method: 'POST',
                            headers: headers,
                            body: JSON.stringify(generatePayload)
                        });
                    }, function (err) {
                        console.error('snapshot failed:', err);
                        exit(1);
                    }, bg.vmFns, {
                        webPoSignalOutput: webPoSignalOutput
                    })
                }, function (err) {
                    console.error('Error loading VM', err);
                    exit(1);
                },
                globalObj[bgChallenge.globalName],
                bgChallenge.program, bgChallenge.userInteractionElement);
        }, function (err) {
            console.error('Could not parse challenge:', err);
            exit(1);
        });
    }, function (err) {
        console.error('Failed to fetch challenge:', err);
        exit(1);
    }, buildURL('Create', false), {
        method: 'POST',
        headers: headers,
        body: JSON.stringify(fetchChallengePayload)
    });
})();
