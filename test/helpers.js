module.exports.decodeB64 = (msg) => {
  return (new Buffer(msg, 'base64')).toString('utf8');
}

module.exports.encodeB64 = (msg) => {
  return (new Buffer(msg)).toString('base64');
}
