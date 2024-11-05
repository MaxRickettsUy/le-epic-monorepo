'use client'

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Release } from "@/lib/types";
import { ChangeEvent, useMemo, useState } from "react";
import _ from 'lodash';
import { Header } from "@/components/ui/header";

interface SelectOption {
  [key: string]: string;
}

const releaseTypes = [
  { value: "full-length", name: "Full Length" },
  { value: "ep", name: "EP" },
  { value: "demo", name: "Demo" },
  { value: "single", name: "Single" },
  { value: "split", name: "Split" }
]

const YearSelect = (props: {
  onChange: (name: string, value: string) => void;
}) => {
  const startYear = 1982;
  const endYear = 2024;

  return (
    <Select onValueChange={(s) => props.onChange('year', s)}>
      <SelectTrigger className="w-[180px]">
        <SelectValue placeholder="Year" />
      </SelectTrigger>
      <SelectContent>
        {Array.from({ length: endYear - startYear + 1 }, (_, index) => {
          const year = startYear + index;
          return (
            <SelectItem key={index} value={`${year}`}>{year}</SelectItem>
          );
        })}
      </SelectContent>
    </Select>
  )
};

const FormSelect = (props: {
  formKey: string;
  label: string;
  options: SelectOption[];
  onChange: (name: string, value: string) => void;
}) => (
  <Select onValueChange={(c) => props.onChange(props.formKey, c)}>
    <SelectTrigger className="w-[180px]">
      <SelectValue placeholder={props.label} />
    </SelectTrigger>
    <SelectContent>
      { props.options.map((o, i) => (
        <SelectItem key={i} value={o.value}>
          {o.name}
        </SelectItem>
      ))}
    </SelectContent>
  </Select>
)

type ReleaseKey = keyof Release;

export default function Page() {
  const [releaseForm, setReleaseForm] = useState<Release>({ } as Release);
  const [typing, setTyping] = useState<boolean>(false);

  const requiredFields: ReleaseKey[] = ["name", "status"];

  const handleInputChange = (key: ReleaseKey, e: ChangeEvent<HTMLInputElement>) => {
    setReleaseForm({
      ...releaseForm,
      [key]: e.target.value === '' ? null : e.target.value
    })

    if (typing) {
      setTyping(false);
    }
  }

  const debounceInput = _.debounce(handleInputChange, 1000)

  const handleSelect = (key: string, value: string) => {
    setReleaseForm({
      ...releaseForm,
      [key]: value
    })
  }

  const handleSubmit = (release: Release) => {
    // const submitBand = async (params: {
    //   release: Release
    // }) => {
    //   const response = await fetch(`${process.env.NEXT_PUBLIC_API_URI}:${process.env.NEXT_PUBLIC_API_PORT}/band/create`, {
    //     method: "POST",
    //     body: JSON.stringify(params.release),
    //     headers: {
    //       "Content-Type": "application/json"
    //     }
    //   })

    //   return response.json();
    // }

    // submitBand({ release }).then((res) => {
    //   console.log(res)
    // })
  }

  const submitDisabled = useMemo(() => {
    let disabled = false;

    requiredFields.forEach((f: ReleaseKey) => {
      if (releaseForm[f] === null || typeof releaseForm[f] === "undefined" ) {
        disabled = true;
      }
    })

    return disabled;
  }, [releaseForm]);

  return (
    <main className="py-[1rem] flex-col">
      <Header />
      <div className="py-[1rem] w-full">
        <Separator />
      </div>
      <div className="flex flex-col gap-[1rem] p-[1rem]">
        <div className="flex flex-row">
          <div className="flex flex-col gap-[1rem]">
            <span className="text-4xl">Add Release</span>
            <Input
              onChange={(e) => {
                if (!typing) {
                  setTyping(true);
                }
                debounceInput('name', e);
              }}
              type="text"
              placeholder="Name"
            />
            <YearSelect onChange={handleSelect} />
            <Input
              onChange={(e) => {
                if (!typing) {
                  setTyping(true);
                }
                debounceInput('label', e);
              }}
              type="text"
              placeholder="Label"
            />
            <FormSelect
              formKey="type"
              label="Release Type"
              onChange={handleSelect}
              options={releaseTypes}
            />
            <Button
              disabled={submitDisabled || typing}
              onClick={() => handleSubmit(releaseForm)}
            >
              Submit
            </Button>
          </div>
        </div>
        <span>{JSON.stringify(releaseForm)}</span>
      </div>
    </main>
  );
}