package main

import (
	"fmt"
	"image"
	"image/color"
	_ "image/jpeg"
	"image/png"
	"os"
	"sort"
	"sync"
)

func check(e error) {
	if e != nil {
		fmt.Println("NOPE")
		panic(e)
	}
}

func main() {
	srcPath := os.Args[1]
	dstPath := os.Args[2]

	reader, err := os.Open(srcPath)
	check(err)
	src, srcFmt, err := image.Decode(reader)
	check(err)
	fmt.Println("Decoded source", srcPath, "as", srcFmt)

	scale := 8
	boundsMax := src.Bounds().Max
	smallMax := boundsMax.Div(scale)

	flat := image.NewNRGBA64(image.Rectangle{image.ZP, smallMax})

	samplePix := func(x, y int) (r, g, b []int) {
		var rs, gs, bs []int
		for i := x - 25; i <= x+25; i += 5 {
			if i < 0 || i >= boundsMax.X {
				continue
			}
			for j := y - 25; j <= y+25; j += 5 {
				if j < 0 || j >= boundsMax.Y {
					continue
				}
				r, g, b, _ := src.At(i, j).RGBA()
				rs = append(rs, int(r))
				gs = append(gs, int(g))
				bs = append(bs, int(b))
			}
		}
		return rs, gs, bs
	}

	var wg sync.WaitGroup
	for i := 0; i < smallMax.X; i++ {
		for j := 0; j < smallMax.Y; j++ {
			wg.Add(1)
			go func(x, y int) {
				defer wg.Done()
				r, g, b := samplePix(x*scale+scale/2, y*scale+scale/2)
				sort.Ints(r)
				sort.Ints(g)
				sort.Ints(b)
				idx := len(r) / 8
				flat.SetNRGBA64(x, y, color.NRGBA64{
					uint16(r[idx]), uint16(g[idx]), uint16(b[idx]),
					0xFFFF})
			}(i, j)
		}
	}
	wg.Wait()

	writer, err := os.OpenFile(dstPath, os.O_WRONLY|os.O_CREATE, 0600)
	check(err)
	//jpeg.Encode(writer, proxy, nil)
	png.Encode(writer, flat)
}
