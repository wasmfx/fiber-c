// The `Wasi` class is taken from this blogpost with minor changes:
// https://dev.to/ndesmic/building-a-minimal-wasi-polyfill-for-browsers-4nel

export class Wasi {
	#argEncodedStrings;
	#instance;
    
	constructor({ args }) {
		// encode args
		this.#argEncodedStrings = [];
		const safeArgs = Array.isArray(args) ? args : [];
		for (let i = 0; i < safeArgs.length; i++) {
			this.#argEncodedStrings.push(this.encodeCString(safeArgs[i]));
		}

		this.bind();
	}

	// helper function to encode a string as a null-terminated C string in a Uint8Array
	encodeCString(s) {
		const str = String(s);
		const bytes = new Uint8Array(str.length + 1);
		for (let i = 0; i < str.length; i++) {
			bytes[i] = str.charCodeAt(i) & 0xff;
		}
		bytes[str.length] = 0;
		return bytes;
	}

	set instance(val) {
		this.#instance = val;
	}

    bind(){
		this.fd_write = this.fd_write.bind(this);
		this.args_get= this.args_get.bind(this);
		this.args_sizes_get = this.args_sizes_get.bind(this);
	}
	
	fd_write(fd, iovsPtr, iovsLength, bytesWrittenPtr) {
		const mem = new Uint8Array(this.#instance.exports.memory.buffer);
		const iovs = new Uint32Array(this.#instance.exports.memory.buffer, iovsPtr, iovsLength * 2);
		let text = "";
		let total = 0;
		// manually decoding bytes to string because TextDecoder isn't available in d8
		for (let i = 0; i < iovsLength * 2; i += 2) {
			const offset = iovs[i];
			const length = iovs[i + 1];
			for (let j = 0; j < length; j++) {
				text += String.fromCharCode(mem[offset + j]);
			}
		total += length;
		}

		new DataView(this.#instance.exports.memory.buffer).setInt32(bytesWrittenPtr, total, true);
		// fd 1 is stdout, so we just log to console
		if (fd === 1) console.log(text);
		return 0;
	}

	proc_exit(code) {
		return 0;
	}
    fd_close(fd) {  
        return 0;
    }
    fd_fdstat_get(fd,buf_ptr) {
        return 0;
    }
    fd_seek(fd, offset, whence, newoffset) { 
        return 0;
    }
	args_sizes_get(argCountPtr, argBufferSizePtr) {
		const argByteLength = this.#argEncodedStrings.reduce((sum, val) => sum + val.byteLength, 0);
		const countPointerBuffer = new Uint32Array(this.#instance.exports.memory.buffer, argCountPtr, 1);
		const sizePointerBuffer = new Uint32Array(this.#instance.exports.memory.buffer, argBufferSizePtr, 1);
		countPointerBuffer[0] = this.#argEncodedStrings.length;
		sizePointerBuffer[0] = argByteLength;
		return 0;
}
	args_get(argsPtr, argBufferPtr) {
		const argsByteLength = this.#argEncodedStrings.reduce((sum, val) => sum + val.byteLength, 0);
		const argsPointerBuffer = new Uint32Array(this.#instance.exports.memory.buffer, argsPtr, this.#argEncodedStrings.length);
		const argsBuffer = new Uint8Array(this.#instance.exports.memory.buffer, argBufferPtr, argsByteLength)
		let pointerOffset = 0;
		for (let i = 0; i < this.#argEncodedStrings.length; i++) {
			const currentPointer = argBufferPtr + pointerOffset;
			argsPointerBuffer[i] = currentPointer;
			argsBuffer.set(this.#argEncodedStrings[i], pointerOffset)
			pointerOffset += this.#argEncodedStrings[i].byteLength;
		}
		return 0;
	}
}

// load the wasm file
const binary = readbuffer(arguments[0]);
// argument to pass to the wasm module, if any
const arg = arguments.length > 1 ? arguments[1] : "";

// import `Wasi` to use it
const wasi = new Wasi({
	// "1" must be passed as first arg for `itersum`, `treesum`, and `sieve`
    args: ["1",arg]
});

WebAssembly.instantiate(binary, { "wasi_snapshot_preview1": wasi }).then(({ instance }) => {
  wasi.instance = instance;
  instance.exports._start();
});