package main

import (
	"fmt"
	"log"
	"strings"
)
import "os"

import "image"
import "image/color"
import "image/jpeg"
import "image/png"

func check(e error) {
	if e != nil {
		log.Fatal(e)
	}
}

func flattenChannel(value1, value2 uint32) uint16 {
	if value1 >= value2/2 {
		return uint16(value1 - value2/2)
	}
	return 0
}

type ProxyImage struct {
	image.Image
	flat image.Image
}

func (p ProxyImage) At(x, y int) color.Color {
	r1, g1, b1, _ := p.Image.At(x, y).RGBA()
	r2, g2, b2, _ := p.flat.At(x, y).RGBA()
	return color.NRGBA64{
		flattenChannel(r1, r2),
		flattenChannel(g1, g2),
		flattenChannel(b1, b2),
		0xFFFF}
}

func main() {
	srcPath := os.Args[1]
	flatPath := os.Args[2]
	dstPath := os.Args[3]

	reader, err := os.Open(srcPath)
	check(err)
	src, srcFmt, err := image.Decode(reader)
	check(err)
	fmt.Println("Decoded source", srcPath, "as", srcFmt)

	reader, err = os.Open(flatPath)
	check(err)
	flat, name, err := image.Decode(reader)
	check(err)
	fmt.Println("Decoded flat", flatPath, "as", name)

	if src.Bounds() != flat.Bounds() {
		log.Fatal("Bounds not equal")
	}

	proxy := ProxyImage{src, flat}

	writer, err := os.OpenFile(dstPath, os.O_WRONLY|os.O_CREATE, 0600)
	check(err)
	if strings.HasSuffix(dstPath, ".jpg") || strings.HasSuffix(dstPath, ".jpeg") {
		jpeg.Encode(writer, proxy, &jpeg.Options{90})
	} else if strings.HasSuffix(dstPath, ".png") {
		png.Encode(writer, proxy)
	} else {
		log.Fatal(dstPath + "does not have .jpg or .png extension")
	}
}
