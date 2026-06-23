def read_u8(data: bytes, offset: int) -> tuple[int, int]:
    return data[offset], offset + 1


def read_i8(data: bytes, offset: int) -> tuple[int, int]:
    value = int.from_bytes(data[offset : offset + 1], "little", signed=True)
    return value, offset + 1


def read_u16(data: bytes, offset: int) -> tuple[int, int]:
    value = int.from_bytes(data[offset : offset + 2], "little")
    return value, offset + 2


def read_i16(data: bytes, offset: int) -> tuple[int, int]:
    value = int.from_bytes(data[offset : offset + 2], "little", signed=True)
    return value, offset + 2


def read_u32(data: bytes, offset: int) -> tuple[int, int]:
    value = int.from_bytes(data[offset : offset + 4], "little")
    return value, offset + 4


def read_i32(data: bytes, offset: int) -> tuple[int, int]:
    value = int.from_bytes(data[offset : offset + 4], "little", signed=True)
    return value, offset + 4
